# -*- coding: utf-8 -*-
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
from rapidocr_onnxruntime import RapidOCR
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
E = RapidOCR()
def ocr(name, region):
    p = os.path.join(ROOT, "out", "live", name)
    if not os.path.exists(p):
        print(name, "missing"); return
    img = cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)
    strip = img[region[0]:region[1], region[2]:region[3]]
    res, _ = E(strip)
    print(name, "->", [str(t) for _, t, _ in (res or [])])
for n in ("research", "layout", "capture", "settings"):
    ocr("qa_%s.png" % n, (-40, None, None, None))
for n in ("zh", "hant", "en"):
    ocr("qa_lang_%s.png" % n, (0, 120, 0, 440))
