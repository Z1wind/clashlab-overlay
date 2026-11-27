# -*- coding: utf-8 -*-
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab.geo import Calib
img = cv2.imdecode(np.fromfile(os.path.join(BASE, "out", "live", "enemy_scout_live.png"), np.uint8), cv2.IMREAD_COLOR)
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
h, s, v = cv2.split(hsv)
m = ((h >= 95) & (h <= 118) & (s >= 160) & (v >= 120)).astype(np.uint8)
ys, xs = np.where(m > 0)
keep = (xs > img.shape[1] * 0.10) & (xs < img.shape[1] * 0.92) & (ys > img.shape[0] * 0.03) & (ys < img.shape[0] * 0.85)
xs, ys = xs[keep], ys[keep]
print("pixels", len(xs))
top = (int(xs[np.argmin(ys)]), int(ys.min()))
bot = (int(xs[np.argmax(ys)]), int(ys.max()))
left = (int(xs.min()), int(ys[np.argmin(xs)]))
right = (int(xs.max()), int(ys[np.argmax(xs)]))
quad = np.array([[top[0], top[1]], [right[0], right[1]], [bot[0], bot[1]], [left[0], left[1]]], np.float32)
print("quad:", quad.tolist())
cal = Calib.from_quad(quad, n=44)
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
        cv2.putText(vis, "%d,%d" % (i, j), (int(p[0]) - 13, int(p[1]) + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1, cv2.LINE_AA)
out = os.path.join(BASE, "out", "live", "grid_wall2.png")
cv2.imencode(".png", vis)[1].tofile(out)
print("saved", out)
