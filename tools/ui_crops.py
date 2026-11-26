# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np, cv2
img = cv2.imdecode(np.fromfile(r"out\live\clan_screen.png", np.uint8), cv2.IMREAD_COLOR)
left = cv2.resize(img[220:420, 0:150], None, fx=3, fy=3, interpolation=cv2.INTER_NEAREST)
cv2.imencode(".png", left)[1].tofile(r"out\live\ui_left.png")
bottom = cv2.resize(img[560:720, 0:760], None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST)
cv2.imencode(".png", bottom)[1].tofile(r"out\live\ui_bottom.png")
print("saved ui_left.png", left.shape, "ui_bottom.png", bottom.shape)
