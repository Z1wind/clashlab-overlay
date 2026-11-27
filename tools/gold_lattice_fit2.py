# -*- coding: utf-8 -*-
"""金顶晶格拟合 v2：按象限约束基向量（等距：u=(+a,+b), v=(-a,+b)），最小残差选尺度。"""
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
for p in pts:
    dd, ii = tree.query(p, k=7, distance_upper_bound=46)
    for dist, j in zip(dd[1:], ii[1:]):
        if not np.isfinite(dist) or j >= len(pts):
            continue
        v = pts[j] - p
        if 12 <= np.linalg.norm(v) <= 46:
            diffs.append(v)
diffs = np.array(diffs, np.float32)
right = diffs[(diffs[:, 0] > 0) & (diffs[:, 1] > 0)]
left = diffs[(diffs[:, 0] < 0) & (diffs[:, 1] > 0)]
print("right:", len(right), "left:", len(left))
def med(vs):
    a = np.median(vs[:, 0]); b = np.median(vs[:, 1])
    return np.array([a, b], np.float32)
u0 = med(right); v0 = med(left)
print("u0", np.round(u0, 2), "v0", np.round(v0, 2))
def residual(M, pts):
    Minv = np.linalg.inv(M)
    ij = pts @ Minv.T
    r = np.abs(ij - np.round(ij)).mean()
    return r
best = None
for su in (0.5, 1.0, 2.0):
    for sv in (0.5, 1.0, 2.0):
        M = np.stack([u0 * su, v0 * sv], axis=1)
        r = residual(M, pts)
        if best is None or r < best[0]:
            best = (r, M)
print("best scale residual:", round(best[0], 4))
R, M = best
Minv = np.linalg.inv(M)
ij = pts @ Minv.T
ijr = np.round(ij)
o = pts.mean(axis=0) - M @ ijr.mean(axis=0)
# 原点细化
bo = None
for dx in np.arange(-30, 31, 2.0):
    for dy in np.arange(-30, 31, 2.0):
        oo = o + np.array([dx, dy], np.float32)
        ij2 = (pts - oo) @ Minv.T
        rr = np.abs(ij2 - np.round(ij2)).mean()
        if bo is None or rr < bo[0]:
            bo = (rr, oo)
res, o = bo
print("origin", np.round(o, 1), "residual", round(float(res), 4))
quad = np.float32([o, o + M @ np.array([44.0, 0.0]), o + M @ np.array([44.0, 44.0]), o + M @ np.array([0.0, 44.0])])
print("quad:", np.round(quad, 1).tolist())
json.dump({"quad": quad.tolist(), "u": M[:, 0].tolist(), "v": M[:, 1].tolist(), "origin": o.tolist()},
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
cv2.imencode(".png", vis)[1].tofile(BASE + r"\out\live\gold_lattice_grid2.png")
print("saved gold_lattice_grid2.png")
