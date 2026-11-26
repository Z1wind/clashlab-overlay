# -*- coding: utf-8 -*-
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
from rapidocr_onnxruntime import RapidOCR
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
E = RapidOCR()
for px in (52, 132, 212, 292):
    p = os.path.join(ROOT, "out", "live", "clean_%d.png" % px)
    if not os.path.exists(p):
        print(px, "missing"); continue
    img = cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)
    res, _ = E(img[-40:, :, :])
    print(px, "->", [str(t) for _, t, _ in (res or [])])
