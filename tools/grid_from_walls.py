# -*- coding: utf-8 -*-
"""用蓝色城墙掩膜求菱形四角 → 44x44 网格标定，输出带刻度图。"""
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab.geo import Calib
img = cv2.imdecode(np.fromfile(os.path.join(BASE, "out", "live", "enemy_scout_live.png"), np.uint8), cv2.IMREAD_COLOR)
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
h, s, v = cv2.split(hsv)
mask = ((h >= 88) & (h <= 128) & (s >= 90) & (v >= 90)).astype(np.uint8) * 255
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
# 全部蓝墙像素合并求最小外接旋转矩形（整圈墙）
ys, xs = np.where(mask > 0)
keep = (xs > img.shape[1] * 0.12) & (xs < img.shape[1] * 0.90) & (ys > img.shape[0] * 0.05) & (ys < img.shape[0] * 0.80)
pts = np.stack([xs[keep], ys[keep]], axis=1).astype(np.float32)
print("wall pixels:", len(pts))
if len(pts) < 500:
    raise SystemExit("too few wall pixels")
rect = cv2.minAreaRect(pts)
box = cv2.boxPoints(rect).astype(np.float32)
c = box.mean(axis=0)
ang = np.arctan2(box[:, 1] - c[1], box[:, 0] - c[0])
box = box[np.argsort(ang)]
ti = int(np.argmin(box[:, 1]))
box = np.roll(box, -ti, axis=0)  # T,R,B,L
print("quad:", np.round(box, 1).tolist())
cal = Calib.from_quad(box, n=44)
vis = img.copy()
for i in range(0, 45):
    p0 = cal.tile_to_px(i, 0); p1 = cal.tile_to_px(i, 44)
    q0 = cal.tile_to_px(0, i); q1 = cal.tile_to_px(44, i)
    col = (0, 255, 0) if i % 4 == 0 else (90, 170, 90)
    cv2.line(vis, (int(p0[0]), int(p0[1])), (int(p1[0]), int(p1[1])), col, 2 if i % 4 == 0 else 1)
    cv2.line(vis, (int(q0[0]), int(q0[1])), (int(q1[0]), int(q1[1])), col, 2 if i % 4 == 0 else 1)
for i in range(0, 45, 4):
    for j in range(0, 45, 4):
        p = cal.tile_to_px(i, j)
        cv2.putText(vis, "%d,%d" % (i, j), (int(p[0]) - 13, int(p[1]) + 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1, cv2.LINE_AA)
out = os.path.join(BASE, "out", "live", "grid_wall.png")
cv2.imencode(".png", vis)[1].tofile(out)
print("saved", out)
