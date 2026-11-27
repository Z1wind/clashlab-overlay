# -*- coding: utf-8 -*-
"""用青色城墙长直线（Hough）拟合村庄菱形四角。"""
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab.geo import Calib
img = cv2.imdecode(np.fromfile(os.path.join(BASE, "out", "live", "enemy_scout_live.png"), np.uint8), cv2.IMREAD_COLOR)
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
h, s, v = cv2.split(hsv)
m = ((h >= 88) & (h <= 108) & (s >= 45) & (s <= 150) & (v >= 150)).astype(np.uint8) * 255
m[:110, :] = 0; m[630:, :] = 0; m[:, :150] = 0; m[:, 1160:] = 0
m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
lines = cv2.HoughLinesP(m, 1, np.pi / 360, threshold=80, minLineLength=140, maxLineGap=10)
pts = []
if lines is not None:
    for x1, y1, x2, y2 in lines.reshape(-1, 4):
        dx, dy = abs(x2 - x1), abs(y2 - y1)
        if dx < 5: continue
        slope = dy / dx
        if 0.2 < slope < 1.2:  # 近菱形边（约 ±0.5 附近）
            pts += [(x1, y1), (x2, y2), ((x1 + x2) / 2, (y1 + y2) / 2)]
print("lines:", 0 if lines is None else len(lines), "pts:", len(pts))
if len(pts) < 20: raise SystemExit("too few")
P = np.array(pts, np.float32)
rect = cv2.minAreaRect(P)
box = cv2.boxPoints(rect).astype(np.float32)
ctr = box.mean(axis=0)
box = box[np.argsort(np.arctan2(box[:, 1] - ctr[1], box[:, 0] - ctr[0]))]
box = np.roll(box, -int(np.argmin(box[:, 1])), axis=0)
print("quad:", np.round(box, 1).tolist())
cal = Calib.from_quad(box, n=44)
vis = img.copy()
for i in range(0, 45):
    p0 = cal.tile_to_px(i, 0); p1 = cal.tile_to_px(i, 44)
    q0 = cal.tile_to_px(0, i); q1 = cal.tile_to_px(44, i)
    col = (0, 255, 0) if i % 4 == 0 else (90, 170, 90)
    cv2.line(vis, (int(p0[0]), int(p0[1])), (int(p1[0]), int(p1[1])), col, 2 if i % 4 == 0 else 1)
    cv2.line(vis, (int(q0[0]), int(q0[1])), (int(q1[0]), int(q1[1])), col, 2 if i % 4 == 0 else 1)
cv2.imencode(".png", vis)[1].tofile(os.path.join(BASE, "out", "live", "grid_hough.png"))
print("saved grid_hough")
