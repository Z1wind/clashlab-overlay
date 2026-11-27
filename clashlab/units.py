# -*- coding: utf-8 -*-
"""兵种 / 法术数据（可视化与模拟共用；粗粒度参考值，用于相对比较）。"""

TROOPS = {
    "miner":        {"zh": "矿工",     "en": "Miner",        "dps": 130, "hp": 1600, "house": 6, "role": "ground", "color": "#7a5cff", "glyph": "矿"},
    "hog-rider":    {"zh": "野猪骑士", "en": "Hog Rider",   "dps": 170, "hp": 1100, "house": 5, "role": "ground", "color": "#b06a3a", "glyph": "猪"},
    "healer":       {"zh": "天使",     "en": "Healer",      "dps": 0,   "hp": 1200, "house": 14, "role": "support", "color": "#ffd7e6", "glyph": "天"},
    "balloon":      {"zh": "气球兵",   "en": "Balloon",     "dps": 240, "hp": 1300, "house": 5, "role": "air", "color": "#c94b4b", "glyph": "气"},
    "edrag":        {"zh": "雷霆飞龙", "en": "Electro Dragon", "dps": 420, "hp": 5000, "house": 30, "role": "air", "color": "#4ab3ff", "glyph": "雷"},
    "dragon":       {"zh": "飞龙",     "en": "Dragon",      "dps": 230, "hp": 4200, "house": 20, "role": "air", "color": "#3f7fd1", "glyph": "龙"},
    "dragon-rider": {"zh": "龙骑士",   "en": "Dragon Rider","dps": 320, "hp": 3800, "house": 40, "role": "air", "color": "#6a4e9c", "glyph": "骑"},
    "root-rider":   {"zh": "根骑士",   "en": "Root Rider",  "dps": 400, "hp": 4500, "house": 20, "role": "ground", "color": "#6b8e23", "glyph": "根"},
    "yeti":         {"zh": "雪怪",     "en": "Yeti",        "dps": 300, "hp": 4500, "house": 18, "role": "ground", "color": "#9fd6f0", "glyph": "雪"},
    "witch":        {"zh": "女巫",     "en": "Witch",       "dps": 140, "hp": 500,  "house": 12, "role": "ground", "color": "#5d3a8a", "glyph": "巫"},
    "super-witch":  {"zh": "超级女巫", "en": "Super Witch", "dps": 260, "hp": 1500, "house": 40, "role": "ground", "color": "#7d4fb0", "glyph": "超"},
    "bowler":       {"zh": "投球手",   "en": "Bowler",      "dps": 120, "hp": 700,  "house": 6, "role": "ground", "color": "#8eb0d1", "glyph": "球"},
    "pekka":        {"zh": "皮卡超人", "en": "P.E.K.K.A",   "dps": 380, "hp": 6500, "house": 25, "role": "ground", "color": "#4b6bd6", "glyph": "皮"},
    "golem":        {"zh": "戈仑石人", "en": "Golem",       "dps": 90,  "hp": 8000, "house": 30, "role": "tank", "color": "#8a7f6f", "glyph": "戈"},
    "ice-golem":    {"zh": "冰戈仑",   "en": "Ice Golem",   "dps": 60,  "hp": 3500, "house": 15, "role": "tank", "color": "#a9dcf0", "glyph": "冰"},
    "valkyrie":     {"zh": "女武神",   "en": "Valkyrie",    "dps": 200, "hp": 1800, "house": 8, "role": "ground", "color": "#e0a13c", "glyph": "武"},
    "wizard":       {"zh": "法师",     "en": "Wizard",      "dps": 130, "hp": 500,  "house": 4, "role": "ranged", "color": "#5a9de0", "glyph": "法"},
    "baby-dragon":  {"zh": "龙宝",     "en": "Baby Dragon", "dps": 110, "hp": 1500, "house": 10, "role": "air", "color": "#7ec8a1", "glyph": "宝"},
    "barbarian":    {"zh": "野蛮人",   "en": "Barbarian",   "dps": 60,  "hp": 400,  "house": 1, "role": "ground", "color": "#c98a3f", "glyph": "野"},
    "archer":       {"zh": "弓箭手",   "en": "Archer",      "dps": 40,  "hp": 250,  "house": 1, "role": "ranged", "color": "#d16ba5", "glyph": "弓"},
    "wall-breaker": {"zh": "炸弹人",   "en": "Wall Breaker", "dps": 90, "hp": 300,  "house": 2, "role": "utility", "color": "#333333", "glyph": "炸"},
}

SPELLS = {
    "rage":          {"zh": "狂暴法术",   "en": "Rage",            "radius": 5, "duration": 20, "use": "提升部队攻速移动", "color": "#e0405a", "glyph": "狂"},
    "freeze":        {"zh": "冰冻法术",   "en": "Freeze",          "radius": 3.5, "duration": 4, "use": "冻结防御 4s", "color": "#67c7f0", "glyph": "冻"},
    "heal":          {"zh": "治疗法术",   "en": "Heal",            "radius": 4.5, "duration": 20, "use": "持续治疗", "color": "#7fd45c", "glyph": "疗"},
    "jump":          {"zh": "弹跳法术",   "en": "Jump",            "radius": 4, "duration": 14, "use": "部队越过城墙", "color": "#e6c447", "glyph": "跳"},
    "haste":         {"zh": "急速法术",   "en": "Haste",           "radius": 4.5, "duration": 16, "use": "大幅提速", "color": "#ff9a3c", "glyph": "急"},
    "clone":         {"zh": "克隆法术",   "en": "Clone",           "radius": 4, "duration": 10, "use": "复制部队", "color": "#b57fe0", "glyph": "克"},
    "poison":        {"zh": "毒药法术",   "en": "Poison",          "radius": 3.5, "duration": 9, "use": "减速/削弱守军", "color": "#8c6ad6", "glyph": "毒"},
    "earthquake":    {"zh": "地震法术",   "en": "Earthquake",      "radius": 3.5, "duration": 1, "use": "拆墙/对建筑比例伤害", "color": "#a9744f", "glyph": "震"},
    "invisibility":  {"zh": "隐形法术",   "en": "Invisibility",    "radius": 4, "duration": 6, "use": "部队/防御不可见", "color": "#7060c9", "glyph": "隐"},
    "skeleton":      {"zh": "骷髅法术",   "en": "Skeleton",        "radius": 3.5, "duration": 12, "use": "召唤骷髅干扰", "color": "#d8d8d8", "glyph": "骷"},
    "bat":           {"zh": "蝙蝠法术",   "en": "Bat",             "radius": 3.5, "duration": 10, "use": "召唤蝙蝠", "color": "#4b3d6b", "glyph": "蝠"},
    "recall":        {"zh": "回溯法术",   "en": "Recall",          "radius": 5, "duration": 8, "use": "回收部队再投放", "color": "#5fb8a8", "glyph": "回"},
    "revive":        {"zh": "复活法术",   "en": "Revive",          "radius": 4, "duration": 10, "use": "复活英雄/部队", "color": "#f0d060", "glyph": "复"},
}

HEROES = {
    "queen":          {"zh": "弓箭女皇",   "en": "Archer Queen",   "color": "#d16ba5", "glyph": "女"},
    "king":           {"zh": "野蛮人之王", "en": "Barbarian King", "color": "#c98a3f", "glyph": "王"},
    "warden":         {"zh": "大守护者",   "en": "Grand Warden",   "color": "#7ec8a1", "glyph": "守"},
    "royal-champion": {"zh": "皇家冠军",   "en": "Royal Champion", "color": "#c94b4b", "glyph": "冠"},
    "minion-prince":  {"zh": "亡灵王子",   "en": "Minion Prince",  "color": "#8c6ad6", "glyph": "亡"},
}


def troop_list():
    return [dict(id=k, **v) for k, v in TROOPS.items()]


def spell_list():
    return [dict(id=k, **v) for k, v in SPELLS.items()]


def hero_list():
    return [dict(id=k, **v) for k, v in HEROES.items()]


def army_dps(army):
    return sum(TROOPS.get(k, {}).get("dps", 80) * v for k, v in (army or {}).items())


def army_hp(army):
    return sum(TROOPS.get(k, {}).get("hp", 600) * v for k, v in (army or {}).items())


# 英雄粗粒度数值（用于模拟；等级按满级近似）
HERO_STATS = {
    "queen":          {"zh": "弓箭女皇",   "dps": 700, "hp": 3800, "ability": {"survival_add": 0.08}},
    "king":           {"zh": "野蛮人之王", "dps": 600, "hp": 4500, "ability": {"dps_mult": 0.08}},
    "warden":         {"zh": "大守护者",   "dps": 300, "hp": 2800, "ability": {"hp_add": 1500}},
    "royal-champion": {"zh": "皇家冠军",   "dps": 650, "hp": 3600, "ability": {"dps_mult": 0.12}},
    "minion-prince":  {"zh": "亡灵王子",   "dps": 500, "hp": 3000, "ability": {"dps_mult": 0.08}},
}

# 法术对模拟的修正（每瓶效果，累加后封顶）
SPELL_EFFECTS = {
    "rage":         {"dps_mult": 0.18, "cap": 0.60},
    "heal":         {"hp_add": 1200, "cap": 6000},
    "freeze":       {"exposure_mult": -0.18, "cap": -0.60},
    "haste":        {"speed_mult": 0.15, "cap": 0.50},
    "jump":         {"wall_cost_mult": -0.25, "cap": -0.85},
    "invisibility": {"exposure_mult": -0.12, "cap": -0.40},
    "clone":        {"dps_mult": 0.10, "cap": 0.30},
    "poison":       {"exposure_mult": -0.08, "cap": -0.30},
    "earthquake":   {"wall_cost_mult": -0.30, "cap": -0.80},
}


def hero_totals(heroes):
    dps = hp = 0.0
    surv = 0.0
    dps_mult = 0.0
    for h in heroes or []:
        s = HERO_STATS.get(h)
        if not s:
            continue
        dps += s["dps"]; hp += s["hp"]
        ab = s.get("ability") or {}
        surv += ab.get("survival_add", 0.0)
        dps_mult += ab.get("dps_mult", 0.0)
        hp += ab.get("hp_add", 0.0)
    return {"dps": dps, "hp": hp, "survival_add": min(0.25, surv), "dps_mult": dps_mult}


def spell_modifiers(spells):
    mods = {"dps_mult": 0.0, "hp_add": 0.0, "exposure_mult": 0.0,
            "speed_mult": 0.0, "wall_cost_mult": 0.0}
    for sid, cnt in (spells or {}).items():
        eff = SPELL_EFFECTS.get(sid)
        if not eff:
            continue
        for k, per in eff.items():
            if k == "cap":
                continue
            cap = eff.get("cap", 0)
            v = per * float(cnt)
            if cap >= 0:
                mods[k] += min(cap, v) if v > 0 else max(-abs(cap), v)
            else:
                mods[k] += max(cap, v)
    return mods
