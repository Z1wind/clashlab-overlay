# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat")
import numpy as np, cv2
from clashlab import ocr_screen
img = cv2.imdecode(np.fromfile(r"out\live\after_boat.png", np.uint8), cv2.IMREAD_COLOR)
for crop in ((0,0,0.42,0.13), (0,0,0.50,0.18), (0,0,0.30,0.16), (0,0,0.55,0.22)):
    lines = ocr_screen.ocr_lines(img, crop=crop)
    print(crop, "->", [(l["text"], l["score"]) for l in lines][:8])
