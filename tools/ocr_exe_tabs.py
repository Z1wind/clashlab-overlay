# -*- coding: utf-8 -*-
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
from rapidocr_onnxruntime import RapidOCR
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
E = RapidOCR()
for n in ("research", "layout", "capture", "settings"):
    p = os.path.join(ROOT, "out", "live", "exe_tab_%s.png" % n)
    if not os.path.exists(p):
        print(n, "missing"); continue
    img = cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)
    res, _ = E(img[-40:, :, :])
    print(n, "->", [str(t) for _, t, _ in (res or [])])
