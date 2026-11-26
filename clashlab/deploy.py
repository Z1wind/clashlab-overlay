# -*- coding: utf-8 -*-
"""放兵点 → 放兵线 / 放兵区域 的候选生成与优化。

用法：
    from clashlab import deploy
    res = deploy.optimize(layout, {"giant": 10, "wizard": 12}, mode="line", trials=12, seed=1)

候选类型：
- point：单点投放（旧行为，作为对照基线）；
- line ：沿一条边撒一条线（4 个点）；
- region：沿一条边的 2×2 区域（4 个点聚成小方块）。
所有随机来自给 seed，结果确定性。
"""
from __future__ import annotations

import math

from . import wargame


def _g(layout):
    if isinstance(layout, dict):
        return int(layout.get("grid") or 44)
    try:
        return int(wargame.load_layout(layout).grid)
    except Exception:
        return 44


def point_candidates(layout):
    g = _g(layout)
    pts = [(1, g // 2), (g - 2, g // 2), (g // 2, 1), (g // 2, g - 2),
           (g // 4, g - 2), (3 * g // 4, g - 2)]
    return [{"id": "point-%d" % i, "kind": "point",
             "points": [p]} for i, p in enumerate(pts)]


def line_candidates(layout):
    g = _g(layout)
    out = []
    spans = [(0.15, 0.85), (0.15, 0.50), (0.50, 0.85)]
    sides = {
        "south": lambda t: (int(round(g * t)), g - 2),
        "north": lambda t: (int(round(g * t)), 1),
        "west": lambda t: (1, int(round(g * t))),
        "east": lambda t: (g - 2, int(round(g * t))),
    }
    for side, fn in sides.items():
        for si, (a, b) in enumerate(spans):
            pts = [fn(a + (b - a) * k / 3.0) for k in range(4)]
            out.append({"id": "line-%s-%d" % (side, si), "kind": "line", "points": pts})
    return out


def region_candidates(layout):
    g = _g(layout)
    out = []
    for cx, cy, name in ((g // 2, g - 3, "south"), (g // 2, 2, "north"),
                         (2, g // 2, "west"), (g - 3, g // 2, "east")):
        pts = [(cx + dx, cy + dy) for dx in (0, 1) for dy in (0, 1)]
        out.append({"id": "region-%s" % name, "kind": "region", "points": pts})
    return out


def candidates(layout, mode="line"):
    mode = str(mode or "line").lower()
    if mode == "point":
        return point_candidates(layout)
    if mode == "region":
        return region_candidates(layout)
    if mode == "all":
        return point_candidates(layout) + line_candidates(layout) + region_candidates(layout)
    return line_candidates(layout)


def evaluate(layout, army, cand, trials=10, seed=1, tick=wargame.DEFAULT_TICK, max_time=wargame.DEFAULT_MAX_TIME,
             troop_levels=None, hero_levels=None):
    """对单个候选跑 trials 次，返回统计。"""
    vals = []
    for k in range(int(trials)):
        r = wargame.simulate_once(layout, army, spawn=cand["points"],
                                  seed=int(seed) * 100000 + k, tick=tick,
                                  max_time=max_time, troop_levels=troop_levels,
                                  hero_levels=hero_levels, collect_events=False)
        vals.append(float(r["destruction"]))
    vals.sort()
    return {"id": cand["id"], "kind": cand["kind"], "points": cand["points"],
            "mean": round(sum(vals) / len(vals), 2),
            "min": vals[0], "max": vals[-1],
            "p10": vals[max(0, int(len(vals) * 0.1) - 1)],
            "p90": vals[min(len(vals) - 1, int(len(vals) * 0.9))]}


def optimize(layout, army, mode="line", trials=10, seed=1, troop_levels=None, hero_levels=None):
    """在候选线/区域里挑摧毁率最高的一条。"""
    cands = candidates(layout, mode)
    rows = [evaluate(layout, army, c, trials=trials, seed=seed,
                     troop_levels=troop_levels, hero_levels=hero_levels) for c in cands]
    rows.sort(key=lambda r: (-r["mean"], r["id"]))
    best = rows[0] if rows else None
    point_rows = [r for r in rows if r["kind"] == "point"]
    baseline = max(point_rows, key=lambda r: r["mean"])["mean"] if point_rows else None
    if baseline is None and mode != "point":
        base = evaluate(layout, army, point_candidates(layout)[0], trials=trials, seed=seed,
                        troop_levels=troop_levels, hero_levels=hero_levels)
        baseline = base["mean"]
    return {"mode": mode, "trials": int(trials), "candidates": rows, "best": best,
            "point_baseline": baseline,
            "gain_vs_point": (round(best["mean"] - baseline, 2) if (best and baseline is not None) else None)}
