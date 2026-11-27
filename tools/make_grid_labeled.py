# -*- coding: utf-8 -*-
"""生成带刻度网格的真实战图，便于按格子读数。"""
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab import calib as C
img = cv2.imdecode(np.fromfile(os.path.join(BASE, "out", "live", "enemy_scout_live.png"), np.uint8), cv2.IMREAD_COLOR)
cal, meta = C.detect_village_quad(img, grid_n=44)
print("method:", meta.get("method"), "quad:", meta.get("quad"))
vis = img.copy()
if cal is not None:
    for i in range(0, 45):
        p0 = cal.tile_to_px(i, 0); p1 = cal.tile_to_px(i, 44)
        q0 = cal.tile_to_px(0, i); q1 = cal.tile_to_px(44, i)
        col = (0, 255, 0) if i % 4 == 0 else (80, 160, 80)
        th = 2 if i % 4 == 0 else 1
        cv2.line(vis, (int(p0[0]), int(p0[1])), (int(p1[0]), int(p1[1])), col, th)
        cv2.line(vis, (int(q0[0]), int(q0[1])), (int(q1[0]), int(q1[1])), col, th)
    for i in range(0, 45, 4):
        for j in range(0, 45, 4):
            p = cal.tile_to_px(i, j)
            cv2.putText(vis, "%d,%d" % (i, j), (int(p[0]) - 14, int(p[1]) + 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 0, 255), 1, cv2.LINE_AA)
out = os.path.join(BASE, "out", "live", "grid_labeled.png")
cv2.imencode(".png", vis)[1].tofile(out)
print("saved", out)
