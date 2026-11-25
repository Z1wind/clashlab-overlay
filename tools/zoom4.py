# -*- coding: utf-8 -*-
"""放大核对素材方报的 4 个防空候选点。"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from clashlab.vision import imread, imwrite
import cv2, numpy as np

img = imread(os.path.join(ROOT, "out/snap/_source/home_village.png"))
OUT = os.path.join(ROOT, "out/snap/annot/ad4")
os.makedirs(OUT, exist_ok=True)
PTS = {"p1_330_215": (330, 215), "p2_1050_385": (1050, 385),
       "p3_360_490": (360, 490), "p4_692_650": (692, 650)}
R = 55
for name, (cx, cy) in PTS.items():
    x0, y0 = max(0, cx - R), max(0, cy - R)
    x1, y1 = min(img.shape[1], cx + R), min(img.shape[0], cy + R)
    crop = img[y0:y1, x0:x1]
    big = cv2.resize(crop, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
    cv2.drawMarker(big, (big.shape[1] // 2, big.shape[0] // 2), (0, 0, 255), cv2.MARKER_CROSS, 30, 3)
    imwrite(os.path.join(OUT, f"{name}.png"), big)
    print(name, "crop", (x0, y0, x1, y1))
