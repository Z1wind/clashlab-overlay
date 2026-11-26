# -*- coding: utf-8 -*-
"""等级缩放：把「等级」换算成 hp/dps 系数。

口径（近似，非官方逐级表）：
- 建筑：hp 每级 ×1.075、dps 每级 ×1.085（上限取 th_data 该 TH 的 reviewed max level）；
- 兵种：hp 每级 ×1.07、dps 每级 ×1.08（TH16 满级约 11）；
- 英雄：每级 ×1.03（满级 95），对军队的加成按「平均英雄等级归一化」的 0..1 亮度映射。

所有函数都是纯函数，越界等级 clamp 到 [1, max_level]，便于在推演里安全使用；
confidence 由调用方在文档/输出里标注。
"""
from __future__ import annotations

BUILDING_HP_GROWTH = 1.075
BUILDING_DPS_GROWTH = 1.085
TROOP_HP_GROWTH = 1.07
TROOP_DPS_GROWTH = 1.08
TROOP_MAX_LEVEL = 11
HERO_GROWTH = 1.03
HERO_MAX_LEVEL = 95
DEFAULT_MAX_LEVEL = 20
# 标注工具/旧布局里的别名 -> ruleset 规范名
ALIASES = {
    "builder-hut": "builders-hut",
    "builder-huts": "builders-hut",
    "dark-spell-factory": "dark-spell-factory",
    "seeking-air-mine": "seeking-air-mine",
}


def clamp_level(level, max_level):
    try:
        lv = int(level)
    except Exception:
        lv = int(max_level)
    mx = max(1, int(max_level or DEFAULT_MAX_LEVEL))
    return max(1, min(lv, mx)), mx


def _ratio(level, max_level, growth):
    lv, mx = clamp_level(level, max_level)
    return float(growth ** (lv - 1)) / float(growth ** (mx - 1))


def building_scale(level, max_level=DEFAULT_MAX_LEVEL):
    """返回建筑在 level 相对 max_level 的 hp/dps 系数（满级 = 1.0）。"""
    return {"hp": _ratio(level, max_level, BUILDING_HP_GROWTH),
            "dps": _ratio(level, max_level, BUILDING_DPS_GROWTH)}


def troop_scale(level, max_level=TROOP_MAX_LEVEL):
    """兵种在 level 相对满级的 hp/dps 系数。"""
    return {"hp": _ratio(level, max_level, TROOP_HP_GROWTH),
            "dps": _ratio(level, max_level, TROOP_DPS_GROWTH)}


def hero_scale(level, max_level=HERO_MAX_LEVEL):
    """英雄等级系数（近似：技能/装备带来的整体强度）。"""
    return _ratio(level, max_level, HERO_GROWTH)


def army_boost(hero_levels):
    """把 {hero: level} 折成对军队的 dps 加成系数（0.5..1.0 线性映射）。

    近似：英雄越接近满级，军队整体输出越接近 100%；低等级按比例打折。
    """
    if not hero_levels:
        return 1.0
    vals = []
    for k, v in dict(hero_levels).items():
        try:
            vals.append(hero_scale(v))
        except Exception:
            continue
    if not vals:
        return 1.0
    avg = sum(vals) / len(vals)
    return 0.5 + 0.5 * avg


def max_level_of(name, th=None, default=DEFAULT_MAX_LEVEL, strict=False):
    """取某建筑在某 TH 的 reviewed 最高等级（优先 knowledge/th_ruleset.json）。

    顺序：ruleset.objects[name].max_levels[str(th)] -> th_data.stats().level -> default。
    """
    th = int(th or 16)
    name = ALIASES.get(str(name), str(name))
    try:
        import json
        import os
        _p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "knowledge", "th_ruleset.json")
        rs = json.load(open(_p, encoding="utf-8"))
        obj = (rs.get("objects") or {}).get(str(name)) or {}
        lv = int((obj.get("max_levels") or {}).get(str(th)) or 0)
        if lv > 0:
            return lv
    except Exception:
        pass
    try:
        from . import th_data
        st = th_data.stats(name, th)
        lv = int(st.get("level") or 0)
        if lv > 0:
            return lv
    except Exception:
        pass
    return None if strict else default
