# -*- coding: utf-8 -*-
"""城墙对称推理：用建筑分布估计对称变换，再镜像补全墙线；区分主城墙与独立墙段。

用法：
    infer_walls(walls, grid=44, ref_points=[建筑 tile...])
    apply_symmetry(layout) -> 补全后的 layout 副本（meta.wall_symmetry 记录推理信息）
"""
from __future__ import annotations

import copy
from collections import deque

GRID = 44
TRANSFORMS = ("mirror-x", "mirror-y", "rot180", "diag")


def _apply(name, x, y, g):
    if name == "mirror-x":      # 左右镜像
        return (g - 1 - x, y)
    if name == "mirror-y":      # 上下镜像
        return (x, g - 1 - y)
    if name == "rot180":
        return (g - 1 - x, g - 1 - y)
    if name == "diag":
        return (y, x)
    return (x, y)


def _overlap(points, name, g):
    s = set(map(tuple, points))
    if not s:
        return 0.0
    return sum(1 for (x, y) in s if _apply(name, x, y, g) in s) / float(len(s))


def best_symmetry(points, grid=GRID, min_overlap=0.5):
    """在 points（建议用建筑 tile）上找最贴合的对称变换。返回 (name, overlap)。"""
    best_name, best = "none", 0.0
    for name in TRANSFORMS:
        sc = _overlap(points, name, grid)
        if sc > best:
            best_name, best = name, sc
    if best < min_overlap:
        return "none", best
    return best_name, best


def infer_walls(walls, grid=GRID, ref_points=None, min_overlap=0.5):
    """补全墙线。ref_points 为空时退化为用墙自身估计对称（要求墙本身已近似对称）。"""
    original = {tuple(map(int, w)) for w in walls}
    ref = list(map(tuple, ref_points)) if ref_points else sorted(original)
    name, score = best_symmetry(ref, grid, min_overlap)
    completed = set(original)
    if name != "none":
        for (x, y) in list(original):
            completed.add(_apply(name, x, y, grid))
    inferred = sorted(completed - original)
    return {"original": len(original), "completed": len(completed),
            "inferred": inferred, "inferred_count": len(inferred),
            "symmetry": name, "score": round(score, 3)}


def _components(cells):
    cells = set(map(tuple, cells))
    seen, comps = set(), []
    for c in cells:
        if c in seen:
            continue
        q, comp = deque([c]), []
        seen.add(c)
        while q:
            x, y = q.popleft()
            comp.append((x, y))
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                n = (x + dx, y + dy)
                if n in cells and n not in seen:
                    seen.add(n)
                    q.append(n)
        comps.append(comp)
    comps.sort(key=len, reverse=True)
    return comps


def main_walls(walls):
    comps = _components(walls)
    return comps[0] if comps else []


def independent_walls(walls):
    comps = _components(walls)
    return [c for comp in comps[1:] for c in comp]


def apply_symmetry(layout, grid=None, min_overlap=0.5):
    """返回补全墙线后的 layout 副本；不会修改传入对象。"""
    g = int(grid or layout.get("grid", GRID))
    walls = layout.get("walls") or []
    ref = [tuple(b.get("tile") or (0, 0)) for b in (layout.get("buildings") or [])]
    info = infer_walls(walls, g, ref_points=ref or None, min_overlap=min_overlap)
    out = copy.deepcopy(layout)
    if info["symmetry"] != "none" and info["inferred_count"]:
        merged = sorted({tuple(map(int, w)) for w in walls} | set(info["inferred"]))
        out["walls"] = [list(w) for w in merged]
    out.setdefault("meta", {})["wall_symmetry"] = {
        k: info[k] for k in ("original", "completed", "inferred_count", "symmetry", "score")}
    return out
