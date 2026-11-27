# -*- coding: utf-8 -*-
"""用「亮绿草地」最大连通块求村庄底板菱形四角，再标定 44 网格。"""
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab.geo import Calib
img = cv2.imdecode(np.fromfile(os.path.join(BASE, "out", "live", "enemy_scout_live.png"), np.uint8), cv2.IMREAD_COLOR)
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
h, s, v = cv2.split(hsv)
m = ((h >= 30) & (h <= 55) & (s >= 80) & (v >= 120)).astype(np.uint8) * 255
m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((31, 31), np.uint8))
m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((15, 15), np.uint8))
n, lab, stats, _ = cv2.connectedComponentsWithStats(m, 8)
bi = max(range(1, n), key=lambda i: stats[i, 4])
print("grass comps", n, "largest area", stats[bi, 4])
comp = (lab == bi).astype(np.uint8) * 255
cnts, _ = cv2.findContours(comp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
c = max(cnts, key=cv2.contourArea)
rect = cv2.minAreaRect(c)
box = cv2.boxPoints(rect).astype(np.float32)
ctr = box.mean(axis=0)
ang = np.arctan2(box[:, 1] - ctr[1], box[:, 0] - ctr[0])
box = box[np.argsort(ang)]
ti = int(np.argmin(box[:, 1]))
box = np.roll(box, -ti, axis=0)
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
        cv2.putText(vis, "%d,%d" % (i, j), (int(p[0]) - 13, int(p[1]) + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 0, 255), 1, cv2.LINE_AA)
cv2.imencode(".png", vis)[1].tofile(os.path.join(BASE, "out", "live", "grid_grass.png"))
print("saved grid_grass")
