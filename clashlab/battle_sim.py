# -*- coding: utf-8 -*-
"""简化战斗模拟（启发式，不是游戏真实引擎）：
 - 寻路：44×44 网格 Dijkstra，墙可破（代价高）、建筑绕行、大本为目标
 - 伤害：路径上防御射程内的 DPS 暴露 × 停留时间 → 部队生存率
 - 输出：进攻侧、路径代价、需破墙数、暴露 DPS、生存率、拆大本时间、粗评级
"""
from __future__ import annotations
import heapq
import math

from .layout_grid import LayoutGrid

N = 44
# 粗粒度兵种数据（来源：社区常见等级量级，用相对比较，非精确值）
TROOP_DPS = {"miner": 130, "hog-rider": 170, "healer": 0, "balloon": 240, "edrag": 420,
             "electro-dragon": 420, "dragon": 230, "dragon-rider": 320, "root-rider": 400,
             "yeti": 300, "witch": 140, "bowler": 120, "pekka": 380, "golem": 90,
             "valkyrie": 200, "wizard": 130, "baby-dragon": 110, "ice-golem": 60,
             "super-witch": 260, "super-wizard": 260, "barbarian": 60, "archer": 40}
TROOP_HP = {"miner": 1600, "hog-rider": 1100, "healer": 1200, "balloon": 1300, "edrag": 5000,
            "electro-dragon": 5000, "dragon": 4200, "dragon-rider": 3800, "root-rider": 4500,
            "yeti": 4500, "witch": 500, "bowler": 700, "pekka": 6500, "golem": 8000,
            "valkyrie": 1800, "wizard": 500, "baby-dragon": 1500, "ice-golem": 3500,
            "super-witch": 1500, "super-wizard": 1500, "barbarian": 400, "archer": 250}
DEF_FALLBACK = {"cannon": (120, 9), "archer-tower": (120, 10), "mortar": (90, 11),
                "wizard-tower": (170, 7), "air-defense": (220, 10), "air-sweeper": (170, 11),
                "x-bow": (200, 11), "inferno-tower": (250, 9), "scattershot": (290, 11),
                "eagle-artillery": (350, 11), "monolith": (300, 8), "spell-tower": (180, 10),
                "multi-archer-tower": (160, 10), "ricochet-cannon": (220, 9), "firespitter": (200, 9)}
WALL_COST = 4.0
BUILDING_COST = 3.0
SPEED = 2.2          # 有效推进速度（格/秒，含破墙停顿）
EXPOSURE_FRAC = 0.55
TH_HP = 6900


def _def_stats(typ):
    try:
        from .assets import STATS
        s = STATS.get(typ) or {}
        dps = float(s.get("dps") or 0)
        rng = float(s.get("range") or 0)
        if dps > 0:
            return dps, rng
    except Exception:
        pass
    return DEF_FALLBACK.get(typ, (0.0, 0.0))


def _grid(layout):
    g = LayoutGrid.from_layout(layout)
    occ = {}
    for b in layout.get("buildings") or []:
        t = b.get("tile") or [0, 0]
        typ = b.get("type") or "unknown"
        x, y = int(round(t[0])), int(round(t[1]))
        for dx in range(2):
            for dy in range(2):
                occ[(x + dx, y + dy)] = typ
    return g, occ


def _dijkstra(g, occ, targets):
    dist = {}
    prev = {}
    pq = []
    for y in range(N):
        for x in range(N):
            if x in (0, N - 1) or y in (0, N - 1):
                dist[(x, y)] = 0.0
                heapq.heappush(pq, (0.0, x, y))
    best = None
    while pq:
        d, x, y = heapq.heappop(pq)
        if d > dist.get((x, y), 1e9):
            continue
        if (x, y) in targets:
            best = (x, y)
            break
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if not (0 <= nx < N and 0 <= ny < N):
                continue
            cost = 1.0
            if (nx, ny) in g.walls:
                cost = WALL_COST
            elif (nx, ny) in occ and occ[(nx, ny)] != "town-hall":
                cost = BUILDING_COST
            nd = d + cost
            if nd < dist.get((nx, ny), 1e9):
                dist[(nx, ny)] = nd
                prev[(nx, ny)] = (x, y)
                heapq.heappush(pq, (nd, nx, ny))
    if best is None:
        return None, [], 0
    path = [best]
    while path[-1] in prev:
        path.append(prev[path[-1]])
    path.reverse()
    walls = sum(1 for (x, y) in path if (x, y) in g.walls)
    return best, path, walls


TH_SCALE = {11: 0.62, 12: 0.70, 13: 0.78, 14: 0.86, 15: 0.93, 16: 1.0, 17: 1.05}


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


def _side_of(p):
    x, y = p
    if x <= 2:
        return "west"
    if x >= N - 3:
        return "east"
    if y <= 2:
        return "north"
    if y >= N - 3:
        return "south"
    return "inner"
