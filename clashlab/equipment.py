# -*- coding: utf-8 -*-
"""equipment.py —— 英雄装备画像（profile）、装备→战术能力约束翻译（profile_rules）、
装备图标模板识别（detect_equipment）。

==================== 诚实边界（写死在模块里，不许绕过） ====================
1. **敌方英雄装备在游戏内不可见**：对战侦察看不到对手英雄穿戴了什么装备，
   本模块对敌方只能输出 ``unknown`` / ``待人工填写``，绝不伪造敌方装备清单。
2. **己方装备**从英雄界面图标识别：模板匹配只给 top-3 候选与分数，
   分数 < 0.7 一律 ``pending``（待人工确认），**人工确认为准**，模块不写死结论。
3. 当前视觉大模型不可用（deepseek-v4.1-flash 不支持图像，视觉模型返回空），
   本模块不依赖任何大模型看图，只做本地模板匹配。
=========================================================================

profile 字段（config/heroes.json，UI 侧也会读写，字段名不要改）::

    {
      "th": 13,
      "heroes": {
        "queen":  {"level": 75, "equipment": ["giant-arrow", "invisibility-vial"]},
        "king":   {"level": 75, "equipment": ["spiky-ball", "earthquake-boots"]},
        "warden": {"level": 50, "equipment": ["eternal-tome", "healing-tome"]},
        "rc":     {"level": 30, "equipment": ["seeking-shield", "hog-rider"]}
      }
    }
"""
import argparse
import json
import os
import sys

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EQUIP_DIR = os.path.join(ROOT, "assets", "coc", "equipment")
DEFAULT_PROFILE_PATH = os.path.join(ROOT, "config", "heroes.json")

# 别名 → 包内规范 id（profile 里允许写简称，识别时解析回规范 id）
EQUIP_ALIASES = {
    "hog-rider": "hog-rider-puppet",
    "vampire-stache": "vampstache",
}

# 识别通过分数线：低于它一律 pending，不写死结论
SCORE_PASS = 0.7
# 模板缩放区间（128px 图标在手机屏上显示约 0.18~0.32 倍）
DETECT_SCALES = (0.18, 0.32)


# --------------------------------------------------------------------------- #
# 装备能力注册表：id -> 基础规则（allowed 仅表示“该策略被此装备解锁”，
# 是否真正启用由 profile 里是否穿戴决定）
# --------------------------------------------------------------------------- #
EQUIP_RULES = {
    "giant-arrow": {
        "hero": "archer-queen",
        "cn": "巨型箭", "en": "Giant Arrow",
        "allowed": True,
        "effect": "启用穿云箭射线规划：按女王朝向规划一条贯穿射线，优先狙杀直线上的关键防御（防空/法师塔/法术塔）",
        "note": "主动技能，需手动瞄准；巨箭直线贯穿，不保证命中射线后方建筑。",
    },
    "invisibility-vial": {
        "hero": "archer-queen",
        "cn": "隐身药水", "en": "Invisibility Vial",
        "allowed": True,
        "effect": "steps 增加『隐身切入时机』：女王进内圈前开启隐身规避火力，打完显形后撤",
        "note": "主动；隐身期间加伤加血，结束后显形，不用于硬吃单点。",
    },
    "spiky-ball": {
        "hero": "barbarian-king",
        "cn": "尖刺球", "en": "Spiky Ball",
        "allowed": True,
        "effect": "蛮王可单点拆核心防御：技能滚动 AoE 清理密集防御群，弹射多个目标",
        "note": "Epic（事件/商人获取）；对集群防御收益高，不做单点普攻替代品。",
    },
    "earthquake-boots": {
        "hero": "barbarian-king",
        "cn": "地震靴", "en": "Earthquake Boots",
        "allowed": True,
        "effect": "允许开墙入点前移 1~2 格：地震破墙与建筑，缩短地面推进距离，免绕墙",
        "note": "主动；地震为范围溅射，对墙体与建筑造成伤害。",
    },
    "eternal-tome": {
        "hero": "grand-warden",
        "cn": "永恒之书", "en": "Eternal Tome",
        "allowed": True,
        "effect": "关键时刻群体无敌窗口：守护者与周围友军免疫伤害，用于扛住爆发火力",
        "note": "主动；只挡伤害不回血，不替代治疗手段。",
    },
    "healing-tome": {
        "hero": "grand-warden",
        "cn": "治疗之书", "en": "Healing Tome",
        "allowed": True,
        "effect": "群体回血窗口：治疗守护者自身与周围友军，用于推进中段抬血续命",
        "note": "主动；范围治疗，有施法范围。",
    },
    "seeking-shield": {
        "hero": "royal-champion",
        "cn": "寻敌盾", "en": "Seeking Shield",
        "allowed": True,
        "effect": "冠军侧翼拆防空：掷盾弹射多目标，优先处理侧翼防空与集群防御",
        "note": "主动；盾牌弹射命中多个目标。",
    },
    "hog-rider-puppet": {
        "hero": "royal-champion",
        "cn": "野猪骑士木偶", "en": "Hog Rider Puppet",
        "allowed": True,
        "effect": "冠军可跳墙：召唤野猪骑士翻墙绕开正面墙体，从侧翼切入",
        "note": "主动；野猪骑士为召唤物，受陷阱与范围伤害。别名 hog-rider。",
    },
    "rage-vial": {
        "hero": "barbarian-king",
        "cn": "狂暴药水", "en": "Rage Vial",
        "allowed": True,
        "effect": "蛮王短时狂暴窗口：加伤+加速，用于定点爆发",
        "note": "主动；无生存加成，不用于承伤。",
    },
    "vampstache": {
        "hero": "barbarian-king",
        "cn": "吸血胡须", "en": "Vampstache",
        "allowed": True,
        "effect": "蛮王普攻回血：延长单人续航，适合长局消耗战",
        "note": "被动；按攻击回血，回不上高 DPS 集火。别名 vampire-stache。",
    },
    "barbarian-puppet": {
        "hero": "barbarian-king",
        "cn": "野蛮人木偶", "en": "Barbarian Puppet",
        "allowed": True,
        "effect": "召唤野蛮人分流火力：吸引防御与陷阱，为主力让路",
        "note": "主动；召唤物脆弱，不承担输出。",
    },
    "giant-gauntlet": {
        "hero": "barbarian-king",
        "cn": "巨拳", "en": "Giant Gauntlet",
        "allowed": True,
        "effect": "蛮王巨化坦克窗口：减伤+地面溅射，正面承伤开路",
        "note": "Epic；主动技能窗口内生效。",
    },
    "snake-bracelet": {
        "hero": "barbarian-king",
        "cn": "蛇形护腕", "en": "Snake Bracelet",
        "allowed": True,
        "effect": "受伤召唤蛇群分流：吸收单体火力，保护主力",
        "note": "Epic；被动触发。",
    },
    "stick-horse": {
        "hero": "barbarian-king",
        "cn": "木马", "en": "Stick Horse",
        "allowed": True,
        "effect": "蛮王被动跳墙+提速攻速：机动绕侧，不被墙体卡住路线",
        "note": "Epic；被动。",
    },
    "archer-puppet": {
        "hero": "archer-queen",
        "cn": "弓箭手木偶", "en": "Archer Puppet",
        "allowed": True,
        "effect": "召唤弓箭手分流：补充远程输出并吸引火力",
        "note": "主动。",
    },
    "healer-puppet": {
        "hero": "archer-queen",
        "cn": "治疗师木偶", "en": "Healer Puppet",
        "allowed": True,
        "effect": "召唤治疗师：女王自我续航，延长单点游走时间",
        "note": "主动。",
    },
    "frozen-arrow": {
        "hero": "archer-queen",
        "cn": "寒冰箭", "en": "Frozen Arrow",
        "allowed": True,
        "effect": "寒冰箭减速窗口：命中区域减速，拖慢防御反应",
        "note": "Epic；主动。",
    },
    "magic-mirror": {
        "hero": "archer-queen",
        "cn": "魔镜", "en": "Magic Mirror",
        "allowed": True,
        "effect": "魔镜分身战术：复制女王分身分担承伤与输出",
        "note": "Epic；主动。",
    },
    "life-gem": {
        "hero": "grand-warden",
        "cn": "生命宝石", "en": "Life Gem",
        "allowed": True,
        "effect": "周围友军额外生命光环：提升团队血量上限",
        "note": "被动。",
    },
    "rage-gem": {
        "hero": "grand-warden",
        "cn": "狂暴宝石", "en": "Rage Gem",
        "allowed": True,
        "effect": "周围友军加伤加速光环：团队输出增益",
        "note": "被动。",
    },
    "fireball": {
        "hero": "grand-warden",
        "cn": "火球", "en": "Fireball",
        "allowed": True,
        "effect": "守护者火球远程打击：补刀远处残血防御",
        "note": "Epic；主动。",
    },
    "haste-vial": {
        "hero": "royal-champion",
        "cn": "急速药水", "en": "Haste Vial",
        "allowed": True,
        "effect": "冠军急速窗口：提速突进，抢点关键建筑",
        "note": "主动。",
    },
    "royal-gem": {
        "hero": "royal-champion",
        "cn": "皇家宝石", "en": "Royal Gem",
        "allowed": True,
        "effect": "冠军大幅回血：自保续航，避免单点被集火倒下",
        "note": "主动。",
    },
    "rocket-spear": {
        "hero": "royal-champion",
        "cn": "火箭矛", "en": "Rocket Spear",
        "allowed": True,
        "effect": "冠军火箭矛远程点杀：超距处理关键防御",
        "note": "Epic；主动。",
    },
}

HERO_SLOTS = ("queen", "king", "warden", "rc")
HERO_CN = {"queen": "弓箭女王", "king": "野蛮人王", "warden": "大守护者", "rc": "皇家冠军"}


# --------------------------------------------------------------------------- #
# profile 读写
# --------------------------------------------------------------------------- #
def default_profile():
    """默认画像：TH13 常用穿戴，仅作首次生成模板，真实装备以人工确认为准。"""
    return {
        "th": 13,
        "heroes": {
            "queen": {"level": 75, "equipment": ["giant-arrow", "invisibility-vial"]},
            "king": {"level": 75, "equipment": ["spiky-ball", "earthquake-boots"]},
            "warden": {"level": 50, "equipment": ["eternal-tome", "healing-tome"]},
            "rc": {"level": 30, "equipment": ["seeking-shield", "hog-rider"]},
        },
    }


def resolve_equip_id(eid):
    """别名解析回规范 id；查不到注册表也原样返回（交给校验报错）。"""
    return EQUIP_ALIASES.get(eid, eid)


def load_profile(path=DEFAULT_PROFILE_PATH):
    """读 profile；文件缺失时回退默认画像（不落盘）。"""
    if not os.path.exists(path):
        return default_profile()
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_profile(profile, path=DEFAULT_PROFILE_PATH):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)
    return path


def ensure_default_profile(path=DEFAULT_PROFILE_PATH):
    """文件不存在时写一份默认画像，返回 profile。"""
    if not os.path.exists(path):
        save_profile(default_profile(), path)
    return load_profile(path)


def _equip_icon_path(eid):
    return os.path.join(EQUIP_DIR, f"{resolve_equip_id(eid)}.png")


def validate_profile(profile):
    """校验 profile：返回 profile 中穿戴但本地缺图的装备 id 列表（未别名解析前的原样 id）。"""
    missing = []
    for slot in HERO_SLOTS:
        entry = profile.get("heroes", {}).get(slot, {})
        for eid in entry.get("equipment", []) or []:
            if not os.path.exists(_equip_icon_path(eid)):
                missing.append(eid)
    return missing


# --------------------------------------------------------------------------- #
# profile_rules：装备 -> 战术能力约束
# --------------------------------------------------------------------------- #
def profile_rules(profile):
    """把穿戴装备翻译成 enabled / disabled 能力约束。

    返回::

        {
          "enabled": [已穿戴且解锁的装备 id...],
          "disabled": [未穿戴或无规则、被禁用的装备 id...],
          "rules": {id: {"allowed", "effect", "note", "hero", "reason"}},
          "missing": [profile 中穿戴但本地缺图的 id...],
          "enemy_equipment": "unknown",
          "enemy_note": "敌方英雄装备在游戏内不可见，只能人工填写或标 unknown，绝不伪造"
        }
    """
    worn = {}  # 规范 id -> 穿戴它的槽位
    for slot in HERO_SLOTS:
        entry = profile.get("heroes", {}).get(slot, {})
        for eid in entry.get("equipment", []) or []:
            worn[resolve_equip_id(eid)] = slot

    rules, enabled, disabled = {}, [], []
    for eid, base in EQUIP_RULES.items():
        worn_slot = worn.get(eid)
        if worn_slot is None:
            # 未穿戴：该策略被禁用，给出原因，不许假装可用
            rules[eid] = {
                "allowed": False,
                "effect": base["effect"],
                "note": base["note"],
                "hero": base["hero"],
                "reason": f"未穿戴 {base['cn']}（{base['en']}），对应策略禁用",
            }
            disabled.append(eid)
        else:
            rules[eid] = {
                "allowed": True,
                "effect": base["effect"],
                "note": base["note"],
                "hero": base["hero"],
                "reason": f"已由 {HERO_CN[worn_slot]}（{worn_slot}）穿戴，策略解锁",
            }
            enabled.append(eid)

    return {
        "enabled": enabled,
        "disabled": disabled,
        "rules": rules,
        "missing": validate_profile(profile),
        "enemy_equipment": "unknown",
        "enemy_note": "敌方英雄装备在游戏内不可见，只能人工填写或标 unknown，绝不伪造",
    }


# --------------------------------------------------------------------------- #
# 模板识别
# --------------------------------------------------------------------------- #
def _imread(path):
    data = np.fromfile(path, dtype=np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_UNCHANGED)


def _list_available_icons():
    out = {}
    if not os.path.isdir(EQUIP_DIR):
        return out
    for f in sorted(os.listdir(EQUIP_DIR)):
        if f.lower().endswith(".png"):
            out[f[:-4]] = os.path.join(EQUIP_DIR, f)
    return out


def detect_equipment(frame, roi=None, scales=DETECT_SCALES, top_k=3):
    """在英雄界面 ROI 里做多尺度模板匹配，返回 top-K 候选 + 分数。

    参数:
        frame: BGR ndarray（已读图）或 None（此时必须用 CLI 的 --image 加载）。
        roi: (x, y, w, h)，只在该区域内匹配；None 则全帧。
        scales: (lo, hi) 模板缩放区间，128px 图标在屏上缩小到该比例。

    返回:
        {"available": bool, "reason": str, "candidates": [...], "threshold": 0.7,
         "pending": bool, "note": "..."}
        素材为空 -> {"available": False, "reason": ...}。
        每个候选: {"id", "score", "scale", "box", "status": "ok"|"pending"}。
        最高候选 < 0.7 -> pending=True，一律标"待人工确认"。
    """
    icons = _list_available_icons()
    if not icons:
        return {"available": False,
                "reason": f"{EQUIP_DIR} 内无装备图标，模板识别不可用；请先运行 scripts/probe_equip_ingest.py",
                "candidates": [], "threshold": SCORE_PASS, "pending": True}

    if frame is None:
        return {"available": False, "reason": "frame 为 None，未提供待识别画面",
                "candidates": [], "threshold": SCORE_PASS, "pending": True}

    if frame.ndim == 3:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    else:
        gray = frame
    if roi:
        rx, ry, rw, rh = roi
        gray = gray[ry:ry + rh, rx:rx + rw]
    gh, gw = gray.shape[:2]

    lo, hi = scales
    n_steps = 9
    scale_list = np.linspace(lo, hi, n_steps)
    rows = []
    for eid, ipath in icons.items():
        tpl = _imread(ipath)
        if tpl is None:
            continue
        if tpl.ndim == 3:
            tg = cv2.cvtColor(tpl, cv2.COLOR_BGRA2GRAY) if tpl.shape[2] == 4 \
                else cv2.cvtColor(tpl, cv2.COLOR_BGR2GRAY)
            mask = ((tpl[:, :, 3] > 40).astype(np.uint8) * 255) if tpl.shape[2] == 4 else None
        else:
            tg, mask = tpl, None
        best = {"score": -1.0, "scale": None, "box": None}
        for s in scale_list:
            tw, th = max(8, int(tg.shape[1] * s)), max(8, int(tg.shape[0] * s))
            if tw >= gw or th >= gh:
                continue
            tr = cv2.resize(tg, (tw, th), interpolation=cv2.INTER_AREA)
            mr = cv2.resize(mask, (tw, th), interpolation=cv2.INTER_AREA) if mask is not None else None
            try:
                res = cv2.matchTemplate(gray, tr, cv2.TM_CCOEFF_NORMED, mask=mr)
            except cv2.error:
                res = cv2.matchTemplate(gray, tr, cv2.TM_CCORR_NORMED)
            res = np.nan_to_num(res, nan=0.0, posinf=0.0, neginf=0.0)
            _, mx, _, mloc = cv2.minMaxLoc(res)
            if mx > best["score"]:
                best = {"score": float(mx), "scale": float(s),
                        "box": (int(mloc[0]), int(mloc[1]), tw, th)}
        rows.append({"id": eid, **best})

    rows.sort(key=lambda r: -r["score"])
    candidates = []
    for r in rows[:top_k]:
        r["score"] = float(np.clip(r["score"], 0.0, 1.0))
        ok = r["score"] >= SCORE_PASS
        candidates.append({
            "id": r["id"],
            "score": round(r["score"], 4),
            "scale": round(r["scale"], 3) if r["scale"] else None,
            "box": r["box"],
            "status": "ok" if ok else "pending",
        })
    top_score = candidates[0]["score"] if candidates else 0.0
    return {
        "available": True,
        "candidates": candidates,
        "threshold": SCORE_PASS,
        "pending": top_score < SCORE_PASS,
        # 模板通道永不自动确认：即使高分候选也必须人工核对后才算数
        "human_confirm_required": True,
        "note": "分数<0.7 一律待人工确认；即便分数>=0.7 也只是高分候选，模板匹配只给候选，人工确认为准",
    }


# --------------------------------------------------------------------------- #
# 独立 CLI：python -m clashlab.equipment detect --image <截图>
# --------------------------------------------------------------------------- #
def _print_table(result):
    if not result.get("available"):
        print("识别不可用:", result.get("reason"))
        return
    print(f"阈值={result['threshold']}  pending={result['pending']}")
    print(f"{'rank':<4}{'id':<22}{'score':<9}{'scale':<8}{'status'}")
    for i, c in enumerate(result["candidates"], 1):
        print(f"{i:<4}{c['id']:<22}{c['score']:<9}{str(c['scale']):<8}{c['status']}")
    if result["pending"]:
        print(">> 最高候选分数低于阈值：待人工确认，不得作为结论")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m clashlab.equipment")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_det = sub.add_parser("detect", help="对一张截图跑装备图标模板识别")
    p_det.add_argument("--image", required=True, help="截图路径")
    p_det.add_argument("--roi", help="x,y,w,h，只匹配该区域")
    p_det.add_argument("--json", action="store_true", help="以 JSON 打印")

    p_prof = sub.add_parser("profile", help="打印 / 生成 / 校验 profile")
    p_prof.add_argument("--path", default=DEFAULT_PROFILE_PATH)
    p_prof.add_argument("--save-default", action="store_true", help="文件缺失时写默认画像")

    args = ap.parse_args(argv)

    if args.cmd == "detect":
        frame = _imread(args.image)
        if frame is None:
            print(f"读图失败: {args.image}")
            return 1
        roi = None
        if args.roi:
            roi = tuple(int(x) for x in args.roi.split(","))
        result = detect_equipment(frame, roi=roi)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            _print_table(result)
        return 0

    if args.cmd == "profile":
        if args.save_default:
            ensure_default_profile(args.path)
        prof = load_profile(args.path)
        missing = validate_profile(prof)
        rules = profile_rules(prof)
        print(json.dumps({"profile": prof, "missing_icons": missing,
                          "enabled": rules["enabled"]}, ensure_ascii=False, indent=2))
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
