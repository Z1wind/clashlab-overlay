# -*- coding: utf-8 -*-
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
from rapidocr_onnxruntime import RapidOCR
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
E = RapidOCR()
p = os.path.join(ROOT, "out", "live", "qa_hant2.png")
img = cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)
res, _ = E(img[0:130, :, :])
print("hant top:", [str(t) for _, t, _ in (res or [])])
