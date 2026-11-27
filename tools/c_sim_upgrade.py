# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "battle_sim.py")
t = open(p, encoding="utf-8").read()
start = t.index("def simulate(layout, army")
end = t.index("def _side_of(p):")
new_sim = '''TH_SCALE = {11: 0.62, 12: 0.70, 13: 0.78, 14: 0.86, 15: 0.93, 16: 1.0, 17: 1.05}


def simulate(layout, army, spells=None, th=None, heroes=None, cc_dps=0.0):
    """启发式战斗模拟。

    spells: {spell_id: count}；th: 大本等级（缩放部队强弱）；heroes: [hero_id,...]。
    """
    from . import units
    g, occ = _grid(layout)
    th_tiles = [p for p, typ in occ.items() if typ == "town-hall"]
    if not th_tiles:
        return {"ok": False, "error": "布局里没有大本(town-hall)"}
    _best, path, walls = _dijkstra(g, occ, set(th_tiles))
    if not path:
        return {"ok": False, "error": "无法到达大本"}
    mods = units.spell_modifiers(spells or {})
    hero = units.hero_totals(heroes or [])
    scale = TH_SCALE.get(int(th), 1.0) if th else 1.0

    wall_cost = max(0.5, WALL_COST * (1.0 + mods.get("wall_cost_mult", 0.0)))
    speed = SPEED * (1.0 + mods.get("speed_mult", 0.0))
    path_cost = 0.0
    for (x, y) in path:
        if (x, y) in g.walls:
            path_cost += wall_cost
        elif (x, y) in occ and occ[(x, y)] != "town-hall":
            path_cost += BUILDING_COST
        else:
            path_cost += 1.0
    time_on_path = path_cost / max(0.5, speed)

    exposure = 0.0
    detail = []
    for b in layout.get("buildings") or []:
        typ = b.get("type") or ""
        dps, rng = _def_stats(typ)
        if dps <= 0 or rng <= 0:
            continue
        t = b.get("tile") or [0, 0]
        cx, cy = float(t[0]) + 1.0, float(t[1]) + 1.0
        near = min((math.hypot(cx - (x + 0.5), cy - (y + 0.5)) for (x, y) in path), default=99)
        if near <= rng:
            exposure += dps
            detail.append({"type": typ, "dist": round(near, 1), "dps": int(dps)})
    exp_mult = max(0.2, 1.0 + mods.get("exposure_mult", 0.0))
    exposure = (exposure + float(cc_dps or 0.0)) * exp_mult

    army_hp = sum(units.TROOPS.get(k, {}).get("hp", TROOP_HP.get(k, 600)) * v for k, v in army.items())
    army_dps = sum(units.TROOPS.get(k, {}).get("dps", TROOP_DPS.get(k, 80)) * v for k, v in army.items())
    army_hp = army_hp * scale + hero["hp"] + mods.get("hp_add", 0.0)
    army_dps = (army_dps + hero["dps"]) * scale * (1.0 + mods.get("dps_mult", 0.0) + hero["dps_mult"])

    dmg = exposure * time_on_path * EXPOSURE_FRAC
    survival = max(0.0, 1.0 - dmg / max(1.0, army_hp))
    survival = min(1.0, survival + hero["survival_add"])
    ttk = TH_HP / max(1.0, army_dps * (0.35 + 0.65 * survival)) + time_on_path * 0.5
    stars = 3 if (survival >= 0.45 and ttk <= 45) else 2 if (survival >= 0.2 and ttk <= 90) else 1
    return {"ok": True, "side": _side_of(path[-1]), "path_len": len(path),
            "walls_to_break": walls, "path_cost": round(path_cost, 1),
            "exposure_dps": int(exposure), "time_on_path_s": round(time_on_path, 1),
            "army_hp": int(army_hp), "army_dps": int(army_dps), "damage_taken": int(dmg),
            "survival": round(survival, 3), "th_ttk_s": round(ttk, 1), "stars_estimate": stars,
            "modifiers": {"th_scale": scale, "spells": mods, "heroes": hero,
                          "cc_dps": float(cc_dps or 0.0), "wall_cost": round(wall_cost, 2)},
            "top_defenses": sorted(detail, key=lambda d: -d["dps"])[:5],
            "note": "启发式估算（粗粒度兵种/英雄/法术表 + 路径暴露），不是真实游戏模拟"}


'''
t = t[:start] + new_sim + t[end:]
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("battle_sim upgraded")
