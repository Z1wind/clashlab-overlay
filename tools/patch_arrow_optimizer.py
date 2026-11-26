# -*- coding: utf-8 -*-
"""穿云箭自动选线：优先串吹风机 + 防空火箭，避开特斯拉当收益。"""
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "overlay", "giant_arrow_diagram.py")
t = open(p, encoding="utf-8").read()

if "def optimize_giant_arrow" in t:
    print("already patched")
else:
    add = '''

# ---------------------------------------------------------------- 自动选线
# 评分口径：吹风机 3 分（影响整片空军路线）> 防空火箭 2 分 > 其它防御 1 分；
# 特斯拉默认不现形，不确定收益，按 -0.5 计（把它穿掉是运气，不是计划）。
_AIR_SCORE = {AIR_SWEEPER: 3.0, AIR_DEFENSE: 2.0}
_OTHER_DEF_SCORE = 1.0
_TESLA_PENALTY = -0.5


def _defense_types():
    try:
        from clashlab import assets
        return set(assets.STATS.keys())
    except Exception:
        return {AIR_DEFENSE, AIR_SWEEPER, "cannon", "archer-tower", "mortar", "wizard-tower",
                "x-bow", "inferno-tower", "scattershot", "eagle-artillery", "monolith",
                "bomb-tower", "hidden-tesla"}


def score_hits(hits):
    """给一组命中打分（越高越好）。"""
    defs = _defense_types()
    s = 0.0
    for h in hits:
        typ = h.get("type")
        if typ in _AIR_SCORE:
            s += _AIR_SCORE[typ]
        elif typ in HIDDEN_TYPES:
            s += _TESLA_PENALTY
        elif typ in defs:
            s += _OTHER_DEF_SCORE
    return round(s, 2)


def _clip_line(p, q, grid=44):
    """把过 p、q 的直线裁到 [0,grid] 方格内，返回端点或 None。"""
    import math as _m
    x1, y1 = float(p[0]), float(p[1])
    x2, y2 = float(q[0]), float(q[1])
    dx, dy = x2 - x1, y2 - y1
    if abs(dx) < 1e-9 and abs(dy) < 1e-9:
        return None
    ts = []
    for bound, d, o in ((0.0, dx, x1), (float(grid), dx, x1), (0.0, dy, y1), (float(grid), dy, y1)):
        if abs(d) > 1e-9:
            tt = (bound - o) / d
            ts.append(tt)
    if not ts:
        return None
    lo, hi = min(ts), max(ts)
    if hi <= lo:
        return None
    a = (x1 + dx * lo, y1 + dy * lo)
    b = (x1 + dx * hi, y1 + dy * hi)
    # 至少要有 6 格长
    if _m.hypot(b[0] - a[0], b[1] - a[1]) < 6:
        return None
    return [round(a[0], 2), round(a[1], 2)], [round(b[0], 2), round(b[1], 2)]


def candidate_arrow_lines(layout, grid=44, tol=1.2):
    """候选箭线：每座对空目标过点的 4 个方向 + 两座对空目标的连线（裁到地图内）。"""
    import math as _m
    air = []
    for b in (layout or {}).get("buildings") or []:
        if isinstance(b, dict) and b.get("type") in AIR_TARGETS:
            try:
                air.append((float(b["tile"][0]), float(b["tile"][1])))
            except Exception:
                continue
    raw = []
    for (x, y) in air:
        for ang in (0, 45, 90, 135):
            rad = _m.radians(ang)
            dx, dy = _m.cos(rad), _m.sin(rad)
            raw.append(((x, y), (x + dx, y + dy)))
    for i in range(len(air)):
        for j in range(i + 1, len(air)):
            raw.append((air[i], air[j]))
    seen = set()
    out = []
    for p, q in raw:
        seg = _clip_line(p, q, grid)
        if not seg:
            continue
        a, b = seg
        key = (round(a[0], 1), round(a[1], 1), round(b[0], 1), round(b[1], 1))
        key2 = (round(b[0], 1), round(b[1], 1), round(a[0], 1), round(a[1], 1))
        if key in seen or key2 in seen:
            continue
        seen.add(key)
        hits = match_skewered(layout, a, b, tol=tol)
        out.append({"from": list(a), "to": list(b), "hits": hits,
                    "score": score_hits(hits), "summary": summarize_hits(hits)})
    out.sort(key=lambda c: (-c["score"], -len(c["hits"]), c["from"][0], c["from"][1]))
    return out


def optimize_giant_arrow(layout, grid=44, tol=1.2, top=5):
    """返回按评分排序的候选箭线；best 为最高分（无对空目标时为空）。"""
    cands = candidate_arrow_lines(layout, grid=grid, tol=tol)
    return {"best": cands[0] if cands else None, "candidates": cands[:int(top)]}
'''
    t = t.rstrip() + "\n" + add
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("optimizer added")
