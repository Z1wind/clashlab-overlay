# -*- coding: utf-8 -*-
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
img = cv2.imdecode(np.fromfile(os.path.join(BASE, "out", "live", "enemy_scout_live.png"), np.uint8), cv2.IMREAD_COLOR)
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
pts = [(640, 62), (760, 120), (980, 250), (300, 250), (200, 330), (640, 600), (900, 450), (420, 420)]
for x, y in pts:
    b, g, r = img[y, x]
    h, s, v = hsv[y, x]
    print((x, y), "BGR", (int(b), int(g), int(r)), "HSV", (int(h), int(s), int(v)))
