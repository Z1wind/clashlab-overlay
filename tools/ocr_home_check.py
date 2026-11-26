# -*- coding: utf-8 -*-
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat")
import numpy as np, cv2
from clashlab import ocr_screen
img = cv2.imdecode(np.fromfile(r"out\live\after_boat.png", np.uint8), cv2.IMREAD_COLOR)
got = ocr_screen.read_opponent(img)
print("home OCR:", {k: got.get(k) for k in ("level", "name", "clan", "tag")})
print("lines:", [l["text"] for l in got["lines"]])
