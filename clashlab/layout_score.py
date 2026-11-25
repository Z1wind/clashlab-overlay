# -*- coding: utf-8 -*-
"""P3b-1：基地布局防守评分（移植 clash-blueprint-engine @clash/analyzer，MIT）。

7 个加权指标（权重和 13）→ 0–100 总分 + S/A/B/C/D/F 等级 + 可定位弱点。
输入只用仓内 layout.json（name/grid/buildings[{type,tile}]/walls[[x,y]]），不依赖游戏。

与原实现的对应关系（逐条移植，非逐行照抄）：
  town-hall-protection  : 100*(0.6*centrality + 0.4*墙圈覆盖率)
  storage-protection    : 100*mean(仓库 centrality)（无仓库给 100）
  air-coverage          : 建筑中心被「可打空」防御射程覆盖比例；按方位弱覆盖点名
  ground-coverage       : 同上，可打地
  compartment-quality   : 100*clamp01((有建筑的隔间数/4)*(1-0.5*死区占比))
  wall-efficiency       : 100*(0.5*墙连通度 + 0.5*隔间内防御占比)
  entry-points          : 有人方位中「无任何伤害防御覆盖」的比例
"""
from __future__ import annotations

import json
import math

GRID_DEFAULT = 44
DEAD_ZONE_MIN_TILES = 4
DIRECTIONS = ("north", "south", "east", "west")

# 防御射程/目标（tile 单位；射程取自 assets.py STATS，目标/伤害类型按游戏常识）。
# damage=False 的（空气炮/法术塔）只影响「不参与覆盖、不算输出」。
DEFENSE_TABLE = {
    "cannon": {"range": 9, "air": False, "ground": True, "damage": True},
    "archer-tower": {"range": 10, "air": True, "ground": True, "damage": True},
    "mortar": {"range": 11, "air": False, "ground": True, "damage": True},
    "air-defense": {"range": 10, "air": True, "ground": False, "damage": True},
    "wizard-tower": {"range": 7, "air": True, "ground": True, "damage": True},
    "bomb-tower": {"range": 6, "air": False, "ground": True, "damage": True},
    "hidden-tesla": {"range": 7, "air": True, "ground": True, "damage": True},
    "x-bow": {"range": 11, "air": True, "ground": True, "damage": True},
    "inferno-tower": {"range": 9, "air": True, "ground": True, "damage": True},
    "scattershot": {"range": 11, "air": False, "ground": True, "damage": True},
    "monolith": {"range": 11, "air": True, "ground": True, "damage": True},
    "multi-archer-tower": {"range": 10, "air": True, "ground": True, "damage": True},
    "ricochet-cannon": {"range": 9, "air": False, "ground": True, "damage": True},
    "firespitter": {"range": 16, "air": False, "ground": True, "damage": True},
    "eagle-artillery": {"range": 11, "air": False, "ground": True, "damage": True},
    "air-sweeper": {"range": 15, "air": True, "ground": False, "damage": False},
    "spell-tower": {"range": 8, "air": True, "ground": True, "damage": False},
}
STORAGE_TYPES = {"gold-storage", "elixir-storage", "dark-elixir-storage"}

METRIC_SPEC = (
    ("town-hall-protection", "大本营保护", 3),
    ("storage-protection", "资源仓保护", 2),
    ("air-coverage", "对空覆盖", 2),
    ("ground-coverage", "对地覆盖", 2),
    ("compartment-quality", "隔间质量", 2),
    ("wall-efficiency", "墙体效率", 1),
    ("entry-points", "入口防守", 1),
)
WEIGHT = {mid: w for mid, _, w in METRIC_SPEC}
METRICS = METRIC_SPEC  # 兼容测试/外部引用的别名

_FOOTPRINT_FALLBACK = {
    "town-hall": 4, "eagle-artillery": 3, "scattershot": 3, "inferno-tower": 2,
    "x-bow": 3, "cannon": 3, "archer-tower": 3, "wizard-tower": 3,
    "air-defense": 3, "mortar": 3, "air-sweeper": 2, "hidden-tesla": 2,
    "bomb-tower": 3, "spell-tower": 2, "multi-archer-tower": 3,
    "monolith": 3, "firespitter": 3, "ricochet-cannon": 3, "clan-castle": 3,
    "gold-storage": 3, "elixir-storage": 3, "dark-elixir-storage": 3,
}


def _footprints():
    """优先用 assets.STATS 的 size（单一真相源），缺的用本地兜底表。"""
    table = dict(_FOOTPRINT_FALLBACK)
    try:
        from .assets import STATS
        for k, v in STATS.items():
            s = v.get("size") if isinstance(v, dict) else None
            if isinstance(s, int) and s > 0:
                table[k] = s
    except Exception:
        pass
    return table


FOOTPRINT = _footprints()


def size_of(btype):
    return FOOTPRINT.get(btype, 3)


def clamp01(v):
    return max(0.0, min(1.0, float(v)))


def grade_for(score):
    if score >= 90:
        return "S"
    if score >= 80:
        return "A"
    if score >= 70:
        return "B"
    if score >= 55:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def load_layout(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------- 几何 ----------------
def centrality(point, grid=GRID_DEFAULT):
    """1 = 正中心，0 = 角落（欧氏距离归一）。"""
    cx = cy = grid / 2.0
    maxd = math.hypot(cx, cy)
    if maxd <= 0:
        return 1.0
    return clamp01(1.0 - math.hypot(point[0] - cx, point[1] - cy) / maxd)


def footprint_bounds(building):
    k = size_of(building.get("type"))
    x, y = building.get("tile") or (0, 0)
    lo_x = int(x) - (k - 1) // 2
    lo_y = int(y) - (k - 1) // 2
    return lo_x, lo_y, k, k


def building_center(building):
    x0, y0, w, h = footprint_bounds(building)
    return (x0 + w / 2.0, y0 + h / 2.0)


def wall_ring_coverage(building, walls, grid=GRID_DEFAULT, size_of=None):
    """建筑足迹外一圈瓦片里墙的占比（0–1）。"""
    x0, y0, w, h = footprint_bounds(building)
    wallset = {(int(a), int(b)) for a, b in walls}
    ring = []
    for x in range(x0 - 1, x0 + w + 1):
        ring.append((x, y0 - 1))
        ring.append((x, y0 + h))
    for y in range(y0, y0 + h):
        ring.append((x0 - 1, y))
        ring.append((x0 + w, y))
    ring = [(x, y) for x, y in ring if 0 <= x < grid and 0 <= y < grid]
    if not ring:
        return 0.0
    return sum(1 for t in ring if t in wallset) / float(len(ring))


def in_range(dpos, tpos, rng):
    return math.hypot(dpos[0] - tpos[0], dpos[1] - tpos[1]) <= rng


def coverage_ratio(targets, defenses, want_air=None, want_ground=None):
    """targets 里被任一符合条件防御覆盖的比例（0–1）。"""
    if want_air is None and want_ground is None:
        sel = lambda d: DEFENSE_TABLE.get(d["type"], {}).get("damage", False)
    else:
        def sel(d):
            info = DEFENSE_TABLE.get(d["type"])
            if not info or not info.get("damage"):
                return False
            if want_air and info.get("air"):
                return True
            if want_ground and info.get("ground"):
                return True
            return False
    if not targets:
        return 1.0
    if not any(sel(d) for d in defenses):
        return 0.0
    hit = 0
    for t in targets:
        for d in defenses:
            if sel(d) and in_range(building_center(d), t, DEFENSE_TABLE[d["type"]]["range"]):
                hit += 1
                break
    return hit / float(len(targets))


def direction_of(point, origin):
    dx, dy = point[0] - origin[0], point[1] - origin[1]
    if abs(dy) >= abs(dx):
        return "north" if dy < 0 else "south"
    return "west" if dx < 0 else "east"


def coverage_by_direction(layout, want_air=None, want_ground=None):
    buildings = layout.get("buildings") or []
    defenses = [b for b in buildings if b.get("type") in DEFENSE_TABLE]
    center = (layout.get("grid", GRID_DEFAULT) / 2.0, layout.get("grid", GRID_DEFAULT) / 2.0)
    buckets = {d: {"total": 0, "covered": 0} for d in DIRECTIONS}
    for b in buildings:
        c = building_center(b)
        d = direction_of(c, center)
        buckets[d]["total"] += 1
        if coverage_ratio([c], defenses, want_air, want_ground) > 0:
            buckets[d]["covered"] += 1
    return buckets


# ---------------- 隔间 ----------------
def analyze_compartments(grid, walls, buildings):
    """从地图四边对非墙格做 4 连通 flood fill；填不到的分量 = 封闭隔间。"""
    grid = int(grid)
    wallset = {(int(x), int(y)) for x, y in walls}
    seen = set()
    comps = []
    for sy in range(grid):
        for sx in range(grid):
            if (sx, sy) in seen or (sx, sy) in wallset:
                continue
            # 只从边界格开始 flood（内部未达格才可能是封闭区）
            pass
    # 边界 flood
    stack = []
    for x in range(grid):
        for y in (0, grid - 1):
            if (x, y) not in wallset and (x, y) not in seen:
                seen.add((x, y)); stack.append((x, y))
    for y in range(grid):
        for x in (0, grid - 1):
            if (x, y) not in wallset and (x, y) not in seen:
                seen.add((x, y)); stack.append((x, y))
    while stack:
        x, y = stack.pop()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < grid and 0 <= ny < grid and (nx, ny) not in wallset and (nx, ny) not in seen:
                seen.add((nx, ny)); stack.append((nx, ny))
    centers = {}
    for b in buildings:
        cx, cy = building_center(b)
        centers[(int(cx), int(cy))] = b
    # 未达格 → 连通分量
    unreached = [(x, y) for y in range(grid) for x in range(grid)
                 if (x, y) not in seen and (x, y) not in wallset]
    unreached_set = set(unreached)
    done = set()
    for cell in unreached:
        if cell in done:
            continue
        comp = []
        stack = [cell]; done.add(cell)
        while stack:
            x, y = stack.pop()
            comp.append((x, y))
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if (nx, ny) in unreached_set and (nx, ny) not in done:
                    done.add((nx, ny)); stack.append((nx, ny))
        ids = [centers[c] for c in comp if c in centers]
        if not ids:
            ids = [b for b in buildings if (int(building_center(b)[0]), int(building_center(b)[1])) in set(comp)]
        comps.append({
            "tile_count": len(comp),
            "building_ids": ids,
            "is_dead_zone": len(comp) >= DEAD_ZONE_MIN_TILES and not ids,
        })
    wall_count = len(wallset)
    isolated = 0
    for (x, y) in wallset:
        if not any((x + dx, y + dy) in wallset for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            isolated += 1
    return {"compartments": comps, "wall_count": wall_count, "isolated_wall_count": isolated}


def wall_efficiency(grid, walls, n_defenses=0, buildings=None):
    comp = analyze_compartments(grid, walls, buildings or [])
    wall_count = comp["wall_count"]
    if wall_count == 0:
        return 0.0
    contiguity = clamp01(1 - comp["isolated_wall_count"] / float(wall_count))
    enclosed_ids = set()
    for c in comp["compartments"]:
        for b in c["building_ids"]:
            enclosed_ids.add(id(b))
    defenses = [b for b in (buildings or []) if b.get("type") in DEFENSE_TABLE]
    enclosed = sum(1 for d in defenses if id(d) in enclosed_ids)
    enclosed_ratio = enclosed / float(len(defenses)) if defenses else 0.0
    return 100.0 * (0.5 * contiguity + 0.5 * enclosed_ratio)


# ---------------- 评分 ----------------
def _metric(mid, label, score, details, weak):
    return {"id": mid, "label": label, "score": round(float(score), 1),
            "weight": WEIGHT[mid], "details": details, "weakPoints": weak}


def score_layout(layout):
    grid = int(layout.get("grid", GRID_DEFAULT))
    buildings = layout.get("buildings") or []
    walls = layout.get("walls") or []
    center = (grid / 2.0, grid / 2.0)
    metrics, weak = [], []

    # 1) 大本营保护
    th = next((b for b in buildings if b.get("type") == "town-hall"), None)
    if th is None:
        metrics.append(_metric("town-hall-protection", "大本营保护", 0,
                               {"centrality": 0, "wallCoverage": 0},
                               [{"severity": "critical", "message": "布局里没有大本营。",
                                 "recommendation": "把大本营放在中心区域。", "area": "overall"}]))
    else:
        c = centrality(building_center(th), grid)
        wr = wall_ring_coverage(th, walls, grid)
        s = 100.0 * (0.6 * c + 0.4 * wr)
        w = []
        if c < 0.5:
            w.append({"severity": "critical" if c < 0.3 else "weak",
                      "message": "大本营偏向 %s 侧，离中心较远。" % direction_of(building_center(th), center),
                      "recommendation": "把大本营往中心挪，让对手多破一层。",
                      "area": direction_of(building_center(th), center)})
        if wr < 0.5:
            w.append({"severity": "weak",
                      "message": "大本营只有 %.0f%% 被墙包围。" % (wr * 100),
                      "recommendation": "给大本营围一圈完整的墙。",
                      "area": "overall"})
        metrics.append(_metric("town-hall-protection", "大本营保护", s,
                               {"centrality": round(c, 2), "wallCoverage": round(wr, 2)}, w))

    # 2) 资源仓保护
    storages = [b for b in buildings if b.get("type") in STORAGE_TYPES]
    if not storages:
        metrics.append(_metric("storage-protection", "资源仓保护", 100.0,
                               {"averageCentrality": 1.0, "exposed": 0},
                               [{"severity": "info", "message": "布局里没有资源仓（纯防御标注）。",
                                 "recommendation": "若做完整布局需补仓库。", "area": "overall"}]))
    else:
        cs = [centrality(building_center(b), grid) for b in storages]
        avg = sum(cs) / len(cs)
        w = []
        for b, c in zip(storages, cs):
            if c < 0.4:
                w.append({"severity": "weak",
                          "message": "%s 暴露在 %s 边缘。" % (b.get("type"), direction_of(building_center(b), center)),
                          "recommendation": "把仓库拉进核心区。", "area": direction_of(building_center(b), center)})
        metrics.append(_metric("storage-protection", "资源仓保护", 100.0 * avg,
                               {"averageCentrality": round(avg, 2), "exposed": len(w)}, w))

    # 3/4) 对空/对地覆盖
    defenses = [b for b in buildings if b.get("type") in DEFENSE_TABLE]
    targets = [building_center(b) for b in buildings]
    for mid, label, kw, layer in (("air-coverage", "对空覆盖", {"want_air": True}, "air"),
                                  ("ground-coverage", "对地覆盖", {"want_ground": True}, "ground")):
        rel = [d for d in defenses if DEFENSE_TABLE[d["type"]].get(layer)]
        if not rel:
            metrics.append(_metric(mid, label, 0.0, {"coverage": 0, "defenses": 0},
                                   [{"severity": "critical",
                                     "message": "这张布局没有%s防御，%s方向全开。" % (
                                         "防空" if layer == "air" else "对地",
                                         "空中" if layer == "air" else "地面"),
                                     "recommendation": "补%s防御。" % ("防空" if layer == "air" else "对地"),
                                     "area": "overall"}]))
            continue
        cov = coverage_ratio(targets, defenses, **kw)
        w = []
        buckets = coverage_by_direction(layout, **kw)
        for d, b in buckets.items():
            if b["total"] >= 2 and b["covered"] / float(b["total"]) < 0.5:
                w.append({"severity": "weak",
                          "message": "%s 侧%s覆盖偏弱（%d/%d 栋被覆盖）。" % (
                              d, "对空" if layer == "air" else "对地", b["covered"], b["total"]),
                          "recommendation": "在该侧补/挪一座%s防御。" % ("防空" if layer == "air" else "对地"),
                          "area": d})
        metrics.append(_metric(mid, label, 100.0 * cov,
                               {"coverage": round(cov, 2), "defenses": len(rel)}, w))

    # 5) 隔间质量
    comp = analyze_compartments(grid, walls, buildings)
    comps = comp["compartments"]
    with_b = [c for c in comps if c["building_ids"]]
    dead = [c for c in comps if c["is_dead_zone"]]
    if not comps:
        metrics.append(_metric("compartment-quality", "隔间质量", 0.0,
                               {"compartments": 0, "deadZones": 0},
                               [{"severity": "weak", "message": "没有闭合隔间——墙没有围出任何区域。",
                                 "recommendation": "把墙连成闭合圈。", "area": "overall"}]))
    else:
        useful = clamp01(len(with_b) / 4.0)
        dead_pen = clamp01(len(dead) / float(len(comps)))
        s = 100.0 * clamp01(useful * (1 - 0.5 * dead_pen))
        w = [{"severity": "info", "message": "有 %d 格空隔间（死区），墙保护了空区域。" % c["tile_count"],
              "recommendation": "把死区并进有建筑的隔间。", "area": "overall"} for c in dead]
        metrics.append(_metric("compartment-quality", "隔间质量", s,
                               {"compartments": len(comps), "useful": len(with_b), "deadZones": len(dead)}, w))

    # 6) 墙体效率
    we = wall_efficiency(grid, walls, len(defenses), buildings)
    w = []
    if comp["isolated_wall_count"]:
        w.append({"severity": "weak",
                  "message": "有 %d 段孤立墙（四邻无墙），没有围出任何区域。" % comp["isolated_wall_count"],
                  "recommendation": "把散墙连进闭合隔间。", "area": "overall"})
    metrics.append(_metric("wall-efficiency", "墙体效率", we,
                           {"walls": comp["wall_count"], "isolated": comp["isolated_wall_count"]}, w))

    # 7) 入口防守
    buckets = coverage_by_direction(layout)
    populated = {d: b for d, b in buckets.items() if b["total"] > 0}
    if not populated:
        metrics.append(_metric("entry-points", "入口防守", 0.0, {"openSides": 0, "sides": 0}, []))
    else:
        open_sides = [d for d, b in populated.items() if b["covered"] == 0]
        s = 100.0 * (1 - len(open_sides) / float(len(populated)))
        w = [{"severity": "weak",
              "message": "%s 侧是完全开放的入口——没有防御覆盖从该方向来的兵。" % d,
              "recommendation": "补一座覆盖 %s 方向来路的防御。" % d, "area": d} for d in open_sides]
        metrics.append(_metric("entry-points", "入口防守", s,
                               {"openSides": len(open_sides), "sides": len(populated)}, w))

    total_w = sum(m["weight"] for m in metrics)
    overall = round(sum(m["score"] * m["weight"] for m in metrics) / total_w, 1) if total_w else 0.0
    order = {"critical": 0, "weak": 1, "info": 2}
    weak_all = [w for m in metrics for w in m["weakPoints"]]
    weak_all.sort(key=lambda w: order.get(w["severity"], 3))
    return {"name": layout.get("name", ""), "overall": overall, "grade": grade_for(overall),
            "metrics": metrics, "weakPoints": weak_all}


def score_path(path):
    return score_layout(load_layout(path))
