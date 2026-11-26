# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "overlay", "giant_arrow_diagram.py")
t = open(p, encoding="utf-8").read()

old_clip = '''def _clip_line(p, q, grid=44):
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
    return [round(a[0], 2), round(a[1], 2)], [round(b[0], 2), round(b[1], 2)]'''
new_clip = '''def _clip_line(p, q, grid=44):
    """把过 p、q 的无限直线用 slab 法裁到 [0,grid]^2，返回端点或 None。"""
    import math as _m
    x1, y1 = float(p[0]), float(p[1])
    x2, y2 = float(q[0]), float(q[1])
    dx, dy = x2 - x1, y2 - y1
    if abs(dx) < 1e-9 and abs(dy) < 1e-9:
        return None
    lo, hi = -1e9, 1e9
    for origin, delta in ((x1, dx), (y1, dy)):
        if abs(delta) < 1e-9:
            if origin < 0 or origin > grid:
                return None
            continue
        t0 = (0.0 - origin) / delta
        t1 = (float(grid) - origin) / delta
        if t0 > t1:
            t0, t1 = t1, t0
        lo = max(lo, t0)
        hi = min(hi, t1)
    if hi - lo < 1e-6:
        return None
    a = (x1 + dx * lo, y1 + dy * lo)
    b = (x1 + dx * hi, y1 + dy * hi)
    if _m.hypot(b[0] - a[0], b[1] - a[1]) < 6:
        return None
    return [round(a[0], 2), round(a[1], 2)], [round(b[0], 2), round(b[1], 2)]'''
if old_clip in t:
    t = t.replace(old_clip, new_clip)
    print("clip fixed")
else:
    print("clip anchor miss")

# 排序：先比吹风机数，再比分
t = t.replace('''    out.sort(key=lambda c: (-c["score"], -len(c["hits"]), c["from"][0], c["from"][1]))''',
'''    out.sort(key=lambda c: (-c["summary"]["air_sweeper"], -c["score"],
                            -len(c["hits"]), c["from"][0], c["from"][1]))''')
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("written")
