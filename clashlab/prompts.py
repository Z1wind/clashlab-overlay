# -*- coding: utf-8 -*-
""""战术提示词工程层：预设人格 + 输出样式 + 压缩上下文 + 缓存。

为什么要单独一层：
1. 大模型在实时/半实时场景最大的敌人不是能力，而是「上下文太长、要求太散」。
   这里把一次复核压到 ≤ 600 token，只给模型它做判断真正需要的信息。
2. 输出必须是固定 schema（JSON），并且带 few-shot 示例，模型一次就能对齐格式，减少重试。
3. 三种样式档位：
   - terse（默认，快）：只要结论 + 入点修正 + 首打顺序，max_tokens 320；
   - coach（教学）：多给一句理由和替代方案，max_tokens 560；
   - audit（审计）：要求逐条挑规则引擎的错，允许否定全部方案，max_tokens 720。
4. 相同（阵型 + 方案 + 样式）的复核结果落盘缓存，2 小时内重复点击不重复计费。
"""
import hashlib
import json
import os
import time

# ---------------- 人格与硬约束 ----------------

BASE_PERSONA = (
    "你是 ClashLab 的战术总监，专精《部落冲突》TH13 联赛进攻。\n"
    "你只看数据说话：网格 44×44（原点左上，x 右 y 下），坐标即格号；"
    "兵种默认 7 只雷龙（edrag），血量 6200，移速 1.5 格/秒。\n"
    "你的判断必须服从三条硬约束：\n"
    "1) 入点只能落在撒兵环（基地包围盒外、不贴建筑），不许放地图四角；\n"
    "2) 双线方案两个入点夹角必须 > 70°，否则会被同一片防空同时罩住；\n"
    "3) 先削防空/鹰火炮/散射炮，再压核心；不要建议先打大本营。\n"
)

SCHEMA = {
    "verdict": "一句话结论，<=40 字，中文",
    "confidence": "0~1 的小数，你对这个结论的把握",
    "entry_adjust": [{"id": "A/B/C", "tile": [8, 16], "reason": "<=25 字"}],
    "strike_order": ["建筑类型(格x,格y)", "..."],
    "risks": ["<=25 字", "..."],
    "notes": "<=80 字补充，可为空",
}

FEW_SHOT = (
    '示例输出：{"verdict":"203° 单点强攻可行，双线更稳","confidence":0.72,'
    '"entry_adjust":[{"id":"B","tile":[36,28],"reason":"与主攻夹角不足，右移两格"}],'
    '"strike_order":["scattershot(32,32)","eagle-artillery(30,14)","air-defense(22,12)"],'
    '"risks":["路径承伤偏高，需先手冰冻"],"notes":"避开重心 (22.5,22.8) 一侧"}'
)

STYLES = {
    "terse": {
        "label": "精简（快）",
        "max_tokens": 340,
        "extra": "只给结论、必要修正和首打顺序；不要复述输入，不要分点解释。",
    },
    "coach": {
        "label": "教练（讲理由）",
        "max_tokens": 600,
        "extra": "每条 entry_adjust 必须给一句可执行理由（先拆什么、为什么这样走位）；notes 给出一句打法节奏建议。",
    },
    "audit": {
        "label": "审计（挑错）",
        "max_tokens": 760,
        "extra": "把它当审计：逐条检查三个方案是否有逻辑错误（入点是否贴角、双线夹角、承伤是否超血量）；"
                 "允许 verdict 直接否定规则引擎，但必须给替代入点和理由。",
    },
}


def style_names():
    return [(k, v["label"]) for k, v in STYLES.items()]


def get_style(name):
    return STYLES.get(name) or STYLES["terse"]


# ---------------- 上下文压缩 ----------------

def compact_brief(layout_name, report, plans, army, max_plans=3):
    """只保留决策必需字段，控制在 600 字内。"""
    troop = army.get("troops", {}).get("edrag", 7)
    lines = [f"阵型 {layout_name}｜{troop} 只雷龙｜核心覆盖 {report.get('core_cover_dps')} dps｜"
             f"重心 ({report.get('centroid', ['-', '-'])[0]},{report.get('centroid', ['-', '-'])[1]})"]
    exp = ", ".join(f"{e['type']}({e['tile'][0]},{e['tile'][1]})" for e in report.get("exposed", [])[:3])
    blind = ", ".join(f"({b['tile'][0]},{b['tile'][1]})" for b in report.get("blind", [])[:2])
    lines.append(f"外露高价值：{exp or '无'}｜盲区：{blind or '无'}")
    for p in plans[:max_plans]:
        ents = " + ".join(f"({e['tile'][0]},{e['tile'][1]})×{e.get('troops', '?')}" for e in p.get("entries", []))
        path = p.get("path") or {}
        lines.append(f"方案{p['id']} {p['name']}：预测 {p.get('predicted')}｜风险 {p.get('risk')}｜"
                     f"入点 {ents}｜{path.get('steps', '-')}格/{path.get('time_s', '-')}s｜承伤 {p.get('exposure', '-')}")
    pri = ", ".join(f"{x['type']}({x['tile'][0]},{x['tile'][1]})" for x in report.get("priority", [])[:3])
    if pri:
        lines.append(f"规则引擎首打顺序：{pri}")
    return "\n".join(lines)


def build_review_messages(brief_text, style="terse", cards=None):
    st = get_style(style)
    system = (
        BASE_PERSONA
        + "只输出一个 JSON 对象，不要 markdown、不要解释、不要在 JSON 外写任何字。\n"
        + "字段规范：" + json.dumps(SCHEMA, ensure_ascii=False) + "\n"
        + "entry_adjust 最多 2 条，坐标必须是整数且在 1~43；没有把握就别改。\n"
        + "参考打法块里的卡仅可在 notes 中按 [kxxx] 原样引用；"
          "没有参考打法块时严禁编造卡号、来源或打法。\n"
        + st["extra"] + "\n"
        + FEW_SHOT
    )
    user = "待复核数据（已压缩，缺的字段就是没有）：\n" + brief_text
    cards_block = build_cards_block(cards)
    if cards_block:
        user += "\n\n" + cards_block
    return [{"role": "system", "content": system}, {"role": "user", "content": user}], st


# ---------------- 视觉标注提示词 ----------------

LABEL_SYSTEM = (
    "你是《部落冲突》阵型识别器。给一张侦察截图，输出建筑清单 JSON。\n"
    "规则：坐标取 44×44 网格格号（左上原点），看不清就给低 conf；"
    "只列真实存在的建筑，不要补全、不要推测；town-hall 用 town-hall，防空用 air-defense。\n"
    "输出格式：{\"buildings\":[{\"type\":\"\",\"tile\":[x,y],\"level\":1,\"conf\":0.8}]}"
)


def build_label_messages(image_b64, hint="44x44"):
    return [{
        "role": "user",
        "content": [
            {"type": "text", "text": LABEL_SYSTEM + f"\n网格：{hint}，只输出 JSON。"},
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + image_b64}},
        ],
    }]


# ---------------- 缓存 ----------------

CACHE_DIR = "out/llm_cache"
CACHE_TTL = 7200


def fingerprint(*parts):
    """配置指纹（P0-06）：army/profile/prebattle/report 等参与缓存键，跨配置不串味。"""
    raw = json.dumps(parts, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def _key(layout_name, plans, style, model_hint="", extra_fp=""):
    # P0-06：旧键只含 {l,s,p,m}，换 army/profile/prebattle 仍撞键；extra_fp 补齐指纹。
    raw = json.dumps({"l": layout_name, "s": style, "p": plans, "m": model_hint,
                      "fp": extra_fp or ""},
                     ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def cache_get(layout_name, plans, style, extra_fp=None):
    fp = fingerprint(extra_fp) if extra_fp else ""
    path = os.path.join(CACHE_DIR, _key(layout_name, plans, style, extra_fp=fp) + ".json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        if time.time() - d.get("t", 0) > CACHE_TTL:
            return None
        return d.get("payload")
    except Exception:
        return None


def cache_put(layout_name, plans, style, payload, extra_fp=None):
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        fp = fingerprint(extra_fp) if extra_fp else ""
        path = os.path.join(CACHE_DIR, _key(layout_name, plans, style, extra_fp=fp) + ".json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"t": time.time(), "payload": payload}, f, ensure_ascii=False)
    except Exception:
        pass


# ---------------- 屏幕绘制补丁提示词（marks，只追加不改旧） ----------------

MARKS_PATCH_SCHEMA = {
    "giant_arrow": {"from": [8, 16], "to": [30, 14], "reason": "<=25字 改动理由，不改可省略"},
    "pins": [{"role": "queen|king|warden|rc|edrag|freeze", "tile": [0, 0]}],
    "steps": ["<=40字 一条动作，最多6条"],
}


def build_marks_messages(brief_text, rule_calls, style="terse", cards=None, prebattle=None):
    """把规则草案当作可编辑基线，要求模型只输出变更补丁（非全量重写）。

    cards: 检索命中的战术卡 [(card, reason)]；prebattle: 赛前简报文本（可选）。
    返回 (messages, style_meta)；style_meta.max_tokens 固定 320，与补丁 schema 匹配。
    模型不可用或补丁非法时由 plan_marks 软失败回退规则结果，本函数不做网络调用。
    """
    st = dict(get_style(style))
    st["max_tokens"] = 320
    system = (
        BASE_PERSONA
        + "你在审阅一份规则引擎已经画好的屏幕标注草案（draw_calls），只输出变更补丁，"
          "不要全量重写，不要复述草案。\n"
        + "允许改：giant_arrow 的 from/to（必须在撒兵环内、from 到 to 直线 ≤32 格、"
          "不得减少穿防空数量）；pins 里个别 role 的站位；steps 的动作顺序与措辞。\n"
        + "没把握就不要改：补丁里省略的字段一律保留规则草案原值。\n"
        + "参考打法块里的卡仅可在 steps 中按 [kxxx] 原样引用；"
          "没有参考打法块时严禁编造卡号、来源或打法。\n"
        + _unknown_block(prebattle)
        + "只输出一个 JSON 对象，不要 markdown、不要解释、不要在 JSON 外写任何字。\n"
        + "补丁 schema：" + json.dumps(MARKS_PATCH_SCHEMA, ensure_ascii=False) + "\n"
        + "from/to 与 pins.tile 都是 1~43 整数格号；steps ≤6 条，每条 ≤40 字。\n"
        + st["extra"] + "\n"
    )
    user = (
        "战况简报：\n" + brief_text
        + "\n\n规则草案（可编辑基线，只给需要改的字段）：\n"
        + json.dumps(rule_calls, ensure_ascii=False)
    )
    cards_block = build_cards_block(cards)
    if cards_block:
        user += "\n\n" + cards_block
    if isinstance(prebattle, dict):
        brief_text = prebattle.get("brief") or ""
        if brief_text:
            user += "\n\n赛前简报（已压缩，仅供参考）：\n" + str(brief_text)[:1200]
    elif prebattle:
        user += "\n\n赛前简报（已压缩，仅供参考）：\n" + str(prebattle)[:1200]
    # P3b-3：布局弱点（大本营偏心/对空/对地）作为可计算事实交给模型，别让它猜
    if isinstance(prebattle, dict):
        try:
            from . import defense_findings as _df
            _block = _df.prompt_block(prebattle)
            if _block:
                user += "\n\n" + _block
        except Exception:
            pass
    user += "\n\n只输出补丁 JSON。"
    return [{"role": "system", "content": system}, {"role": "user", "content": user}], st


def _unknown_block(prebattle):
    """prebattle info dict 的 unknown 清单原样写进 system；不是 dict 返回空串。"""
    if not isinstance(prebattle, dict):
        return ""
    unknown = prebattle.get("unknown") or []
    if not unknown:
        return ""
    return ("以下信息未知，不要假设：" + "、".join(str(u) for u in unknown)
            + "；steps 不得依赖未知项，若必须依赖要在理由里注明。\n")


# ---------------- 战术卡注入块（只追加） ----------------

def build_cards_block(cards, max_cards=3):
    """把检索到的战术卡压成"参考打法（来源 id）"块，供 review/marks 两类消息复用。

    cards: [(card, reason)] 或 card dict 列表；每卡 ≤3 行，最多 3 卡；
    conf<0.5 必须带"未验证"标记，source.note 一并给出；无卡片返回空串。
    """
    if not cards:
        return ""
    lines = ["参考打法（来源 id，仅供参考；conf<0.5 为未验证，不可直接照抄）："]
    n = 0
    for item in cards:
        if n >= max_cards:
            break
        card = item[0] if isinstance(item, tuple) else item
        cid = card.get("id", "?")
        conf = card.get("confidence")
        conf_txt = f"conf {conf:.2f}" if isinstance(conf, (int, float)) else "conf ?"
        unverified = "，未验证" if (isinstance(conf, (int, float)) and conf < 0.5) else ""
        src = card.get("source") or {}
        kp = (card.get("key_points") or [""])[0]
        lines.append(f"[{cid}] {card.get('pattern') or '-'} {conf_txt}{unverified} — {kp[:60]}")
        note = src.get("note", "")
        if note:
            lines.append(f"    来源：{src.get('site', '')} {note}")
        n += 1
    return "\n".join(lines)


# ---------------- 结构化展示 ----------------

def to_cards(review):
    """把校验后的复核结果变成 UI 能直接渲染的结构块。"""
    if not review:
        return []
    out = []
    if review.get("verdict"):
        out.append({"kind": "verdict", "text": review["verdict"]})
    conf = review.get("confidence")
    if isinstance(conf, (int, float)):
        out.append({"kind": "confidence", "value": round(float(conf), 2)})
    for it in review.get("entry_adjust") or []:
        out.append({"kind": "adjust", "id": it.get("id", ""), "tile": it.get("tile"),
                    "text": it.get("reason", "")})
    if review.get("strike_order"):
        out.append({"kind": "order", "items": review["strike_order"]})
    if review.get("risks"):
        out.append({"kind": "risk", "items": review["risks"]})
    if review.get("notes"):
        out.append({"kind": "note", "text": review["notes"]})
    return out
