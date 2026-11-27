# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "layout_grid.py")
t = open(p, encoding="utf-8").read()
old = '''def _polyline_points(walls):
    """兼容多种墙表示：[[x,y],...] 折线、{'points': [...]}、tile 列表。"""
    pts = []
    for w in walls or []:
        if isinstance(w, dict):
            seq = w.get("points") or w.get("polyline") or w.get("tiles") or []
        elif isinstance(w, (list, tuple)) and w and isinstance(w[0], (list, tuple)):
            seq = w
        else:
            seq = [w]
        for p in seq:
            if isinstance(p, (list, tuple)) and len(p) >= 2:
                pts.append((float(p[0]), float(p[1])))
    return pts'''
new = '''def _is_point(v):
    return isinstance(v, (list, tuple)) and len(v) >= 2 and not isinstance(v[0], (list, tuple))


def _segments_to_polyline(points):
    """平铺点列表可能是「折线」也可能是「两两配对的线段端点」，用平均段长判断。"""
    if len(points) < 4:
        return points
    consec = [math.hypot(points[i + 1][0] - points[i][0], points[i + 1][1] - points[i][1])
              for i in range(len(points) - 1)]
    pairs = [math.hypot(points[i + 1][0] - points[i][0], points[i + 1][1] - points[i][1])
             for i in range(0, len(points) - 1, 2)]
    avg_consec = sum(consec) / max(1, len(consec))
    avg_pair = sum(pairs) / max(1, len(pairs))
    if len(points) % 2 == 0 and avg_pair > avg_consec * 1.8 and avg_pair >= 3.0:
        # 端点配对：展开成 起点->终点->起点... 的折线（彼此不相连也无妨，栅格采样按段处理）
        flat = []
        for i in range(0, len(points) - 1, 2):
            flat.append(points[i]); flat.append(points[i + 1])
        return flat
    return points


def _polyline_points(walls):
    """兼容多种墙表示：[[x,y],...] 折线 / 两两线段端点 / {'points': [...]} / tile 列表。"""
    pts = []
    for w in walls or []:
        if isinstance(w, dict):
            seq = w.get("points") or w.get("polyline") or w.get("tiles") or []
            pts.extend(_flatten(seq))
        elif _is_point(w):
            pts.append((float(w[0]), float(w[1])))
        elif isinstance(w, (list, tuple)):
            pts.extend(_flatten(w))
    return _segments_to_polyline(pts)


def _flatten(seq):
    out = []
    for p in seq or []:
        if _is_point(p):
            out.append((float(p[0]), float(p[1])))
    return out'''
if old in t:
    t = t.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("walls parser upgraded")
else:
    print("anchor miss")
