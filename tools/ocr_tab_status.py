# -*- coding: utf-8 -*-
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
from rapidocr_onnxruntime import RapidOCR
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
E = RapidOCR()
for name in ("research", "layout", "capture", "settings"):
    p = os.path.join(ROOT, "out", "live", "mf_%s.png" % name)
    img = cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)
    strip = img[-40:, :, :]
    res, _ = E(strip)
    texts = [str(t) for _, t, _ in (res or [])]
    print(name, "->", texts)
