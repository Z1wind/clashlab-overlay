# -*- coding: utf-8 -*-
"""B-1：用城墙像素 + 主方向拟合菱形四边求四角（1080p 家园截图）。"""
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
IMG = os.path.join(BASE, "out", "live", "hires", "coc_193842_6.png")
img = cv2.imdecode(np.fromfile(IMG, np.uint8), cv2.IMREAD_COLOR)
h, w = img.shape[:2]
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
white = cv2.inRange(hsv, (0, 0, 155), (180, 55, 255))
orange = cv2.inRange(hsv, (8, 110, 130), (32, 255, 255))
mask = cv2.bitwise_or(white, orange)
# UI 区域排除（左右面板、顶栏、底部按钮条）
mask[:90, :] = 0
mask[:, :345] = 0
mask[:, 1680:] = 0
mask[895:, :] = 0
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
# Hough 估主方向
lines = cv2.HoughLinesP(mask, 1, np.pi / 180, threshold=90, minLineLength=140, maxLineGap=18)
angles = []
if lines is not None:
    for l in lines[:400]:
        arr = np.asarray(l).reshape(-1)
        if arr.size < 4:
            continue
        x1, y1, x2, y2 = arr[:4]
        dx, dy = x2 - x1, y2 - y1
        if abs(dx) < 20 or abs(dy) < 12:
            continue
        a = np.degrees(np.arctan2(dy, dx))
        angles.append(a)
angles = [a for a in angles if 8 < abs(a) < 70]
med = float(np.median([abs(a) for a in angles])) if angles else 30.0
m = float(np.tan(np.radians(med)))
print("lines:", 0 if lines is None else len(lines), "angles median(deg):", round(med, 2), "m:", round(m, 3), flush=True)
ys, xs = np.nonzero(mask)
print("wall px:", len(xs), flush=True)
# 两条斜率的截距
c = ys - m * xs          # 斜率 +m
d = ys + m * xs          # 斜率 -m
def q(v, pct):
    return float(np.percentile(v, pct))
c1, c2 = q(c, 0.5), q(c, 99.5)
d1, d2 = q(d, 0.5), q(d, 99.5)
def inter(cv1, dv1):
    # y = m x + cv1 ; y = -m x + dv1
    x = (dv1 - cv1) / (2 * m)
    y = m * x + cv1
    return [x, y]
TL = inter(c1, d1); TR = inter(c1, d2); BR = inter(c2, d2); BL = inter(c2, d1)
quad = np.float32([TL, TR, BR, BL])
print("quad TL,TR,BR,BL:", [[round(v, 1) for v in p] for p in quad], flush=True)
# 画网格检查
sys.path.insert(0, BASE)
from clashlab.geo import Calib
cal = Calib.from_quad(quad, n=44)
vis = img.copy()
for i in range(0, 45, 2):
    p1 = cal.tile_to_px(i, 0); p2 = cal.tile_to_px(i, 44)
    cv2.line(vis, (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), (0, 0, 255), 1)
    q1 = cal.tile_to_px(0, i); q2 = cal.tile_to_px(44, i)
    cv2.line(vis, (int(q1[0]), int(q1[1])), (int(q2[0]), int(q2[1])), (0, 0, 255), 1)
cv2.polylines(vis, [quad.astype(np.int32)], True, (255, 0, 255), 2)
cv2.imencode(".png", vis)[1].tofile(os.path.join(BASE, "out", "live", "hires_hough_grid.png"))
json.dump({"quad": quad.tolist(), "m": m, "angle_deg": med}, open(os.path.join(BASE, "out", "live", "hires_hough_quad.json"), "w"), ensure_ascii=False, indent=1)
print("saved hires_hough_grid.png")
