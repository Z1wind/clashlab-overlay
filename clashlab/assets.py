# -*- coding: utf-8 -*-
"""素材层：官方建筑/兵种 PNG（透明底）+ 近似数值表 + 模板匹配。

素材来源：npm 包 clash-of-clans-data（MIT，图片版权归 Supercell，仅按 Fan Content
Policy 用于本地非商业研究）。图片按 基地/分类/建筑/等级 存放，见 assets/coc。
"""
import logging
import os
import numpy as np
import cv2

_log = logging.getLogger("clashlab.assets")

_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "coc")
BUILD_ROOT = os.path.join(_ROOT, "buildings")
ICON_ROOT = os.path.join(_ROOT, "icons")

# 建筑近似数值：对标 13 本（TH13）。hp 与 dps 只用于相对排序，不追求逐级精确。
STATS = {
    "town-hall":        {"cn": "大本营",   "size": 4, "hp": 6900, "dps": 0,   "range": 0,  "level": 13},
    "eagle-artillery":  {"cn": "鹰火炮",   "size": 3, "hp": 4000, "dps": 350, "range": 11, "level": 3},
    "scattershot":      {"cn": "散射炮",   "size": 3, "hp": 3000, "dps": 290, "range": 11, "level": 2},
    "inferno-tower":    {"cn": "地狱塔",   "size": 2, "hp": 3200, "dps": 250, "range": 9,  "level": 6},
    "x-bow":            {"cn": "X 连弩",   "size": 3, "hp": 3000, "dps": 200, "range": 11, "level": 6},
    "cannon":           {"cn": "加农炮",   "size": 3, "hp": 1200, "dps": 118, "range": 9,  "level": 16},
    "archer-tower":     {"cn": "箭塔",     "size": 3, "hp": 1400, "dps": 118, "range": 10, "level": 16},
    "wizard-tower":     {"cn": "法师塔",   "size": 3, "hp": 1300, "dps": 122, "range": 7,  "level": 13},
    "air-defense":      {"cn": "防空",     "size": 3, "hp": 1500, "dps": 330, "range": 10, "level": 10},
    "mortar":           {"cn": "迫击炮",   "size": 3, "hp": 1000, "dps": 45,  "range": 11, "level": 13},
    "air-sweeper":      {"cn": "吹风机",   "size": 2, "hp": 1050, "dps": 0,   "range": 0,  "level": 7},
    "hidden-tesla":     {"cn": "特斯拉",   "size": 2, "hp": 1000, "dps": 130, "range": 7,  "level": 10},
    "bomb-tower":       {"cn": "炸弹塔",   "size": 3, "hp": 1600, "dps": 90,  "range": 6,  "level": 6},
    # 2026-11-25 size 3→2：上游 base-validator ruleset(home-2026-11-17, reviewed) 判 2x2；
    # 其 art manifest 由真实精灵包围盒量得 width_tiles=1.994 —— 两处独立证据一致。
    "spell-tower":      {"cn": "法术塔",   "size": 2, "hp": 2500, "dps": 120, "range": 8,  "level": 2},
    "multi-archer-tower": {"cn": "多重箭塔", "size": 3, "hp": 1600, "dps": 140, "range": 10, "level": 2},
}

# ---------------------------------------------------------------------------
# TH16 覆盖表（只给 stats(name, th=16) 取数用，绝不回写 STATS）
#
# 为什么单独放：STATS 是 TH13 基线，被 building_path()（assets.py:51）按 level 拼 PNG
# 路径、被 api._valid_type() 当类型白名单；把 TH16 等级/新建筑塞进 STATS 会让图标
# 找不到、类型校验语义改变。因此 TH16 数值只进本表，building_path 继续只读 STATS。
# level 仅用于展示，不参与任何文件路径拼接。
# ---------------------------------------------------------------------------
TH16_OVERRIDE = {
    "monolith": {
        "hp": 5353, "dps": 193, "range": 11, "level": 3,
        "source_url": "https://clashofclans.fandom.com/wiki/Monolith",
        "source_site": "Clash of Clans Wiki (Fandom)",
        "fetched_at": "2026-11-23",
        "confidence": "high",
        "note": ("TH16 可升最高 Lv3（Lv1 HP4747/DPS150，Lv2 HP5050/DPS175）。"
                 "dps=193 为 wiki『基础每秒伤害』口径，不含每发 13% 目标最大生命附加伤害"
                 "（单发基础 289.5）；射程 11 格，单体，对地对空，攻速 1.5s。"
                 "反坦克/反英雄威胁主要来自百分比附加伤害，非基础 dps。"),
    },
    "firespitter": {
        "hp": 4500, "dps": 410, "range": 16, "level": 1,
        "source_url": "https://clashofclans.fandom.com/wiki/Firespitter",
        "source_site": "Clash of Clans Wiki (Fandom)",
        "fetched_at": "2026-11-23",
        "confidence": "low",
        "note": ("TH17 解锁（2024-11-25 加入），TH16 不可建造；TH16_OVERRIDE 中仅作"
                 "前瞻/兼容登记，TH16 阵型排序不应命中。以下为现行 Lv1 参考值，非 TH16 "
                 "数值，故置信度 low。dps=410 为游戏内近似 burst 均值（20 发/轮×46 伤害、"
                 "轮间 1.0167s、每发可穿 2 目标、对地对空）；射程 16 格，单向约 150° 扇形。"),
    },
    "ricochet-cannon": {
        "hp": 5700, "dps": 390, "range": 9, "level": 2,
        "source_url": "https://clashofclans.fandom.com/wiki/Ricochet_Cannon",
        "source_site": "Clash of Clans Wiki (Fandom)",
        "fetched_at": "2026-11-23",
        "confidence": "high",
        "note": ("TH16 可升最高 Lv2（Lv1 HP5400/DPS360，Supercell 官方 TH16 博客同源："
                 "https://supercell.com/en/games/clashofclans/blog/game-updates/building-merging-th16/）。"
                 "dps=390 为对主目标每秒伤害；弹跳副目标在主目标 3.5 格内、伤害衰减 30%"
                 "（Lv2 副目标 218.4/发）；射程 9 格，单体对地，攻速 0.8s。"),
    },
    "clan-castle": {
        "hp": 5600, "dps": 0, "range": 0, "level": 12,
        "source_url": "https://clashofclans.fandom.com/wiki/Clan_Castle",
        "source_site": "Clash of Clans Wiki (Fandom)",
        "fetched_at": "2026-11-23",
        "confidence": "high",
        "note": ("TH16 可升最高 Lv12；本身不攻击，dps=0、range=0，仅存放援兵（50 人口）/"
                 "法术（3 格）/攻城机器（2 格），受击后援兵出击。"),
    },
}

# 未知建筑兜底（旧本地模式的硬编码值，analysis.py:60 / prebattle.py:69 同款）
DEFAULT_FALLBACK = {"hp": 1400, "dps": 120, "range": 9}

_missing_warned = set()


def stats(name, th=None):
    """按本数取数，返回 dict（含 hp / dps / range 键）。

    - th=16 且 name 命中 TH16_OVERRIDE：STATS 基线（若有）+ 覆盖值合并，
      hp/dps/range/level 以 TH16 为准，cn/size 等沿用基线；
    - th=None 或其它值：返回 STATS 基线；缺失再回 DEFAULT_FALLBACK。
    - name 两边都没有时记 WARN（模块级 set 去重，只 WARN 一次）。

    注意：本函数只读 STATS / TH16_OVERRIDE，不写回，也不影响 building_path。
    """
    base = STATS.get(name)
    if th == 16 and name in TH16_OVERRIDE:
        out = dict(base) if base else {}
        out.update(TH16_OVERRIDE[name])
        return out
    if base is not None:
        return dict(base)
    if name not in _missing_warned:
        _missing_warned.add(name)
        _log.warning("assets.stats: 未知建筑类型 %r（无 STATS 基线、无 TH16_OVERRIDE），"
                     "回退 DEFAULT_FALLBACK", name)
    return dict(DEFAULT_FALLBACK)

# 模板匹配的候选（只取辨识度高的，避免误检堆满屏）
ANCHORS = ["town-hall", "eagle-artillery", "scattershot", "inferno-tower", "x-bow",
           "air-defense", "wizard-tower", "archer-tower", "cannon", "mortar"]

_tpl_cache = {}


def bgra(path):
    """透明底 PNG 读入为 BGRA；用 fromfile 避开中文路径。"""
    data = np.fromfile(path, dtype=np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_UNCHANGED)


def building_path(name, level=None):
    d = os.path.join(BUILD_ROOT, name)
    if not os.path.isdir(d):
        return None
    lv = level if level is not None else STATS.get(name, {}).get("level", 1)
    p = os.path.join(d, f"level-{lv}.png")
    if os.path.exists(p):
        return p
    # 回退到最近的可用等级
    files = sorted((f for f in os.listdir(d) if f.startswith("level-")),
                   key=lambda f: abs(int(f.split("-")[-1].split(".")[0]) - lv))
    return os.path.join(d, files[0]) if files else None


def icon_path(kind, name):
    for ext in (".png",):
        p = os.path.join(ICON_ROOT, kind, name + ext)
        if os.path.exists(p):
            return p
    return None


def load_template(name, level=None):
    key = (name, level)
    if key in _tpl_cache:
        return _tpl_cache[key]
    p = building_path(name, level)
    if not p:
        return None
    img = bgra(p)
    if img is None:
        return None
    _tpl_cache[key] = img
    return img


def _prep(frame):
    g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(g)


def match_buildings(frame, tile_px, names=None, scales=None, thresh=0.5, max_per_type=8):
    """多尺度模板匹配。tile_px 是一格在屏幕上的像素宽，用来推模板缩放。"""
    names = names or ANCHORS
    gray = _prep(frame)
    fh, fw = gray.shape[:2]
    hits = []
    if scales is None:
        # 一个 3x3 建筑在屏幕上大约占 3 格宽，模板原始宽约 200px，据此推基础倍率
        base = (tile_px * 3.2) / 200.0
        scales = [base * k for k in (0.7, 0.85, 1.0, 1.15, 1.3)]

    for name in names:
        tpl = load_template(name)
        if tpl is None:
            continue
        for s in scales:
            tw, th = int(tpl.shape[1] * s), int(tpl.shape[0] * s)
            if tw < 12 or th < 12 or tw >= fw or th >= fh:
                continue
            t = cv2.resize(tpl, (tw, th), interpolation=cv2.INTER_AREA)
            alpha = t[:, :, 3]
            mask = (alpha > 40).astype(np.uint8) * 255
            tg = cv2.cvtColor(t, cv2.COLOR_BGRA2GRAY)
            if mask.sum() == 0:
                continue
            # 用带掩膜的相关归一化，透明区域不参与打分
            res = cv2.matchTemplate(gray, tg, cv2.TM_CCORR_NORMED, mask=mask)
            res = np.nan_to_num(res, nan=0.0, posinf=0.0, neginf=0.0)
            loc = np.where(res >= thresh)
            for y, x in zip(*loc):
                hits.append({"type": name, "score": float(res[y, x]), "box": (int(x), int(y), tw, th),
                             "scale": float(s)})

    # 按类型做贪心非极大值抑制
    hits.sort(key=lambda h: -h["score"])
    kept = []
    for h in hits:
        bx, by, bw, bh = h["box"]
        cx, cy = bx + bw / 2, by + bh * 0.7
        dup = False
        for k in kept:
            kx, ky = k["box"][0] + k["box"][2] / 2, k["box"][1] + k["box"][3] * 0.7
            if ((cx - kx) ** 2 + (cy - ky) ** 2) ** 0.5 < max(bw, bh) * 0.55:
                dup = True
                break
        if not dup:
            kept.append(h)
    # 每类限量，避免同一建筑被多个尺度重复记
    out, cnt = [], {}
    for h in sorted(kept, key=lambda h: -h["score"]):
        c = cnt.get(h["type"], 0)
        if c >= max_per_type:
            continue
        cnt[h["type"]] = c + 1
        out.append(h)
    return out
