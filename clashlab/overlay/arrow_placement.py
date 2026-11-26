# -*- coding: utf-8 -*-
"""英雄落点 → 最近目标 → 穿云箭方向（含落点敏感性测试）。

游戏机制（必须谨慎）：
- 英雄部署后优先打**最近的中心**（距离按建筑中心算）；
- 穿云箭方向由英雄当前朝向决定，实际就是「英雄 → 最近建筑中心」这条线；
- 落点偏移 0.1 格都可能改变最近目标，进而改变整条箭线命中的建筑。

约定：layout["buildings"][i]["tile"] 是**建筑中心**（本仓标注工具按中心点击）。
若来源是左上角坐标，用 center_mode="corner" 自动按建筑尺寸换算。
"""
from __future__ import annotations

import math

from . import giant_arrow_diagram as _ga


def _size_of(typ):
    try:
        return _ga._size_of(typ)
    except Exception:
        return 3


def building_center(b, center_mode="center"):
    """返回建筑中心 (x, y)。center_mode=corner 时用尺寸/2 换算。"""
    x, y = float(b["tile"][0]), float(b["tile"][1])
    if center_mode == "corner":
        s = _size_of(b.get("type"))
        x += (s - 1) / 2.0
        y += (s - 1) / 2.0
    return x, y


def nearest_building(layout, queen_tile, center_mode="center"):
    """按中心距离找最近建筑；返回 dict 或 None。"""
    qx, qy = float(queen_tile[0]), float(queen_tile[1])
    best = None
    for b in (layout or {}).get("buildings") or []:
        if not isinstance(b, dict):
            continue
        tile = b.get("tile")
        if not (isinstance(tile, (list, tuple)) and len(tile) == 2):
            continue
        try:
            cx, cy = building_center(b, center_mode)
        except Exception:
            continue
        d = math.hypot(cx - qx, cy - qy)
        if best is None or d < best["dist"]:
            best = {"type": b.get("type") or "", "tile": [int(round(cx)), int(round(cy))],
                    "center": [round(cx, 2), round(cy, 2)], "dist": round(d, 3)}
    return best


def _extend(qx, qy, dx, dy, grid=44):
    """从 (qx,qy) 沿 (dx,dy) 到地图边界；返回边界点与角度。"""
    if abs(dx) < 1e-9 and abs(dy) < 1e-9:
        return None, 0.0
    lo, hi = -1e9, 1e9
    for o, d in ((qx, dx), (qy, dy)):
        if abs(d) < 1e-9:
            continue
        t0 = (0.0 - o) / d
        t1 = (float(grid) - o) / d
        if t0 > t1:
            t0, t1 = t1, t0
        lo = max(lo, t0)
        hi = min(hi, t1)
    if hi - lo < 1e-6:
        return None, 0.0
    t = hi if hi > 0 else lo
    return [round(qx + dx * t, 2), round(qy + dy * t, 2)], round(math.degrees(math.atan2(dy, dx)), 1)


def arrow_from_placement(layout, queen_tile, grid=44, tol=1.2, center_mode="center"):
    """英雄落点 -> (最近目标, 箭线, 命中列表)。"""
    tgt = nearest_building(layout, queen_tile, center_mode=center_mode)
    qx, qy = float(queen_tile[0]), float(queen_tile[1])
    if tgt is None:
        return {"queen": [round(qx, 2), round(qy, 2)], "target": None, "from": None, "to": None,
                "angle_deg": None, "hits": [], "summary": _ga.summarize_hits([]), "score": 0.0}
    cx, cy = tgt["center"]
    dx, dy = cx - qx, cy - qy
    to, ang = _extend(qx, qy, dx, dy, grid=grid)
    hits = _ga.match_skewered(layout, [qx, qy], to, tol=tol) if to else []
    return {"queen": [round(qx, 2), round(qy, 2)], "target": tgt,
            "from": [round(qx, 2), round(qy, 2)], "to": to, "angle_deg": ang,
            "hits": hits, "summary": _ga.summarize_hits(hits), "score": _ga.score_hits(hits)}


def _signature(res):
    tgt = (res.get("target") or {}).get("type")
    hits = tuple(sorted((h["type"], h["tile"][0], h["tile"][1]) for h in res.get("hits") or []))
    return (tgt, hits)


def placement_sensitivity(layout, queen_tile, radius=0.5, step=0.25, grid=44, tol=1.2,
                          center_mode="center"):
    """在落点周围 ±radius 格采样，统计最近目标/箭线命中是否翻转。

    游戏里落点微调就换目标，所以实机前必须看 stable 与 flips。
    """
    import itertools
    offs = []
    n = int(round(radius / step)) if step > 0 else 0
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            offs.append((round(i * step, 3), round(j * step, 3)))
    variants = []
    sigs = {}
    for dx, dy in offs:
        qx = float(queen_tile[0]) + dx
        qy = float(queen_tile[1]) + dy
        res = arrow_from_placement(layout, [qx, qy], grid=grid, tol=tol, center_mode=center_mode)
        sig = _signature(res)
        sigs.setdefault(sig, []).append({"offset": [dx, dy], "angle_deg": res.get("angle_deg"),
                                         "target": (res.get("target") or {}).get("type"),
                                         "hits": len(res.get("hits") or [])})
        variants.append({"offset": [dx, dy], "target": (res.get("target") or {}).get("type"),
                         "angle_deg": res.get("angle_deg"), "hits": res.get("hits") or []})
    base = variants[offs.index((0.0, 0.0))] if (0.0, 0.0) in offs else variants[0]
    flips = [v for v in variants if (v["target"] != base["target"])]
    return {"stable": len(sigs) == 1, "samples": len(variants),
            "distinct_signatures": len(sigs), "flips": len(flips),
            "variants": variants}
