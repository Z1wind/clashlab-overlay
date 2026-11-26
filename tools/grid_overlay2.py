# -*- coding: utf-8 -*-
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np, cv2
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
img = cv2.imdecode(np.fromfile(os.path.join(BASE, "out", "live", "enemy_scout_live.png"), np.uint8), cv2.IMREAD_COLOR)
for x in range(0, 1280, 100):
    cv2.line(img, (x, 0), (x, 720), (0, 255, 255), 1)
    cv2.putText(img, str(x), (x + 2, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 255), 1)
for y in range(0, 720, 100):
    cv2.line(img, (0, y), (1280, y), (0, 255, 255), 1)
    cv2.putText(img, str(y), (2, y + 12), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 255), 1)
out = os.path.join(BASE, "out", "live", "grid_overlay.png")
cv2.imencode(".png", img)[1].tofile(out)
print("saved", out)
