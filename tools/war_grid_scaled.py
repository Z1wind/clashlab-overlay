# -*- coding: utf-8 -*-
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab.geo import Calib
import cv2, numpy as np
IMG = os.path.join(BASE, "out", "live", "hires", "scout_enemybase_202650.png")
img = cv2.imdecode(np.fromfile(IMG, np.uint8), cv2.IMREAD_COLOR)
quad = np.float32([[960, 78], [1680, 528], [960, 978], [267, 528]])
cal = Calib.from_quad(quad, n=44)
vis = img.copy()
for i in range(0, 45, 2):
    p1 = cal.tile_to_px(i, 0); p2 = cal.tile_to_px(i, 44)
    cv2.line(vis, (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), (0, 0, 255), 1)
    q1 = cal.tile_to_px(0, i); q2 = cal.tile_to_px(44, i)
    cv2.line(vis, (int(q1[0]), int(q1[1])), (int(q2[0]), int(q2[1])), (0, 0, 255), 1)
cv2.imencode(".png", vis)[1].tofile(os.path.join(BASE, "out", "live", "hires_war_grid_scaled.png"))
print("saved")
