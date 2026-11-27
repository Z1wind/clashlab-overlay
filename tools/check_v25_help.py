# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
from rapidocr_onnxruntime import RapidOCR
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
img = cv2.imdecode(np.fromfile(BASE + r"\out\apk_qa\v25_help.png", np.uint8), cv2.IMREAD_COLOR)
E = RapidOCR(); res, _ = E(img)
for b, t, s in (res or []):
    ts = str(t)
    if "v0.2" in ts or "双击" in ts or "30" in ts:
        print(ts)
