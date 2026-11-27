# -*- coding: utf-8 -*-
"""金顶晶格拟合：从金顶中心估计 44x44 网格（基向量+原点），输出 quad 并画图验证。"""
import json, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
from scipy.spatial import cKDTree
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
IMG = BASE + r"\out\live\war1080\base_01_215536.png"
img = cv2.imdecode(np.fromfile(IMG, np.uint8), cv2.IMREAD_COLOR)
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
mask = cv2.inRange(hsv, (15, 140, 150), (35, 255, 255))
mask[:90, :] = 0; mask[:, :340] = 0; mask[:, 1700:] = 0; mask[900:, :] = 0
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
num, lab, stats, cents = cv2.connectedComponentsWithStats(mask, 8)
pts = []
for i in range(1, num):
    x, y, ww, hh, area = stats[i]
    if 6 <= area <= 120 and 0.4 <= ww / max(1, hh) <= 2.5:
        pts.append(cents[i])
pts = np.array(pts, np.float32)
tree = cKDTree(pts)
diffs = []
for i, p in enumerate(pts):
    dd, ii = tree.query(p, k=7, distance_upper_bound=46)
    for dist, j in zip(dd[1:], ii[1:]):
        if not np.isfinite(dist) or j >= len(pts):
            continue
        v = pts[j] - p
        if np.linalg.norm(v) < 12:
            continue
        diffs.append(v)
diffs = np.array(diffs, np.float32)
ang = np.degrees(np.arctan2(diffs[:, 1], diffs[:, 0])) % 180
# 两个主方向（模 180 聚类）
hist, edges = np.histogram(ang, bins=36, range=(0, 180))
peaks = np.argsort(hist)[::-1][:8]
# 找两个相隔 >20 度的峰
dirs = []
for pk in peaks:
    a = (edges[pk] + edges[pk + 1]) / 2
    if all(min(abs(a - d), 180 - abs(a - d)) > 20 for d in dirs):
        dirs.append(a)
    if len(dirs) == 2:
        break
print("dominant dirs(deg):", [round(d, 1) for d in dirs])
def basis_for(a):
    sel = np.abs(((ang - a + 90) % 180) - 90) < 8
    vs = diffs[sel]
    if len(vs) < 10:
        return None
    # 取中位数向量（按方向统一符号）
    u = np.median(vs, axis=0)
    u = u / np.linalg.norm(u) * np.median(np.linalg.norm(vs, axis=1))
    return u.astype(np.float32)
u = basis_for(dirs[0]); v = basis_for(dirs[1])
print("basis u:", None if u is None else np.round(u, 2), "v:", None if v is None else np.round(v, 2))
if u is not None and v is not None:
    M = np.stack([u, v], axis=1)  # 2x2
    Minv = np.linalg.inv(M)
    ij = pts @ Minv.T
    frac = ij - np.round(ij)
    res = np.abs(frac - np.round(frac))
    print("lattice residual mean:", round(float(res.mean()), 4), "p90:", round(float(np.percentile(res, 90)), 4))
    # 原点：使坐标落在 0..44
    ijr = np.round(ij)
    o = pts.mean(axis=0) - M @ ijr.mean(axis=0)
    print("origin approx:", np.round(o, 1))
    # 原点细化：最小化残差
    best = None
    for dx in np.arange(-20, 21, 2.0):
        for dy in np.arange(-20, 21, 2.0):
            oo = o + np.array([dx, dy], np.float32)
            ij2 = (pts - oo) @ Minv.T
            r = np.abs(ij2 - np.round(ij2)).mean()
            if best is None or r < best[0]:
                best = (r, oo)
    res, o = best
    print("refined origin:", np.round(o, 1), "residual:", round(float(res), 4))
    quad = np.float32([o, o + M @ np.array([44.0, 0.0]), o + M @ np.array([44.0, 44.0]), o + M @ np.array([0.0, 44.0])])
    print("quad:", np.round(quad, 1).tolist())
    json.dump({"quad": quad.tolist(), "u": u.tolist(), "v": v.tolist(), "origin": o.tolist()},
              open(BASE + r"\out\live\gold_lattice_quad.json", "w"), ensure_ascii=False, indent=1)
    sys.path.insert(0, BASE)
    from clashlab.geo import Calib
    cal = Calib.from_quad(quad, n=44)
    vis = img.copy()
    for k in range(0, 45, 2):
        p1 = cal.tile_to_px(k, 0); p2 = cal.tile_to_px(k, 44)
        cv2.line(vis, (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), (0, 0, 255), 1)
        q1 = cal.tile_to_px(0, k); q2 = cal.tile_to_px(44, k)
        cv2.line(vis, (int(q1[0]), int(q1[1])), (int(q2[0]), int(q2[1])), (0, 0, 255), 1)
    cv2.polylines(vis, [quad.astype(np.int32)], True, (255, 0, 255), 2)
    cv2.imencode(".png", vis)[1].tofile(BASE + r"\out\live\gold_lattice_grid.png")
    print("saved gold_lattice_grid.png")
