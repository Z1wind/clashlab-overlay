# -*- coding: utf-8 -*-
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
from rapidocr_onnxruntime import RapidOCR
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
img = cv2.imdecode(np.fromfile(os.path.join(BASE, "out", "live", "hires", "war_enemy2_202604.png"), np.uint8), cv2.IMREAD_COLOR)
E = RapidOCR(); res, _ = E(img)
for box, txt, score in (res or []):
    xs = [p[0] for p in box]; ys = [p[1] for p in box]
    print("%-18s conf=%.2f center=(%d,%d)" % (str(txt), score, sum(xs)/4, sum(ys)/4))
