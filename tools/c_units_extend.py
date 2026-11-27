# -*- coding: utf-8 -*-
"""C：模拟升级（英雄/装备/法术/援军 + 多配比对比）。"""
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"

# 1) units.py 追加英雄/法术效果数据
p = os.path.join(BASE, "clashlab", "units.py")
t = open(p, encoding="utf-8").read()
if "HERO_STATS" not in t:
    t += '''

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
'''
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("units.py extended")
