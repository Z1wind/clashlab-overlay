# -*- coding: utf-8 -*-
"""在 manual2 标定下生成 4 张放大分块图（带格心编号），便于逐块读建筑坐标。"""
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab.geo import Calib
img = cv2.imdecode(np.fromfile(os.path.join(BASE, "out", "live", "enemy_scout_live.png"), np.uint8), cv2.IMREAD_COLOR)
quad = np.array([[640.0, 52.0], [1120.0, 352.0], [640.0, 652.0], [178.0, 352.0]], np.float32)
cal = Calib.from_quad(quad, n=44)
vis = img.copy()
for i in range(45):
    p0 = cal.tile_to_px(i, 0); p1 = cal.tile_to_px(i, 44)
    q0 = cal.tile_to_px(0, i); q1 = cal.tile_to_px(44, i)
    cv2.line(vis, (int(p0[0]), int(p0[1])), (int(p1[0]), int(p1[1])), (0, 255, 0), 1)
    cv2.line(vis, (int(q0[0]), int(q0[1])), (int(q1[0]), int(q1[1])), (0, 255, 0), 1)
for gi in range(0, 45, 2):
    for gj in range(0, 45, 2):
        c = cal.tile_to_px(gi + 0.5, gj + 0.5)
        cv2.putText(vis, "%d,%d" % (gi, gj), (int(c[0]) - 10, int(c[1]) + 3), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 1, cv2.LINE_AA)
x0, y0 = 120, 40
crops = {"q_tl": (0, 0), "q_tr": (1, 0), "q_bl": (0, 1), "q_br": (1, 1)}
w, h = 600, 380
for name, (cx, cy) in crops.items():
    x = x0 + cx * (w - 40); y = y0 + cy * (h - 40)
    crop = vis[y:y + h, x:x + w]
    crop = cv2.resize(crop, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
    cv2.imencode(".png", crop)[1].tofile(os.path.join(BASE, "out", "live", name + ".png"))
    print(name, "x", x, "y", y)
