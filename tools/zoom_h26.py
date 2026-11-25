# -*- coding: utf-8 -*-
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from clashlab.vision import imread, imwrite
import cv2
img = imread(os.path.join(ROOT, "out/snap/_source/home_village.png"))
R = 55
for name, (cx, cy) in {"h26_612_392": (612, 392)}.items():
    x0, y0 = max(0, cx - R), max(0, cy - R)
    x1, y1 = min(img.shape[1], cx + R), min(img.shape[0], cy + R)
    crop = img[y0:y1, x0:x1]
    big = cv2.resize(crop, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
    cv2.drawMarker(big, (big.shape[1] // 2, big.shape[0] // 2), (0, 0, 255), cv2.MARKER_CROSS, 30, 3)
    imwrite(os.path.join(ROOT, "out/snap/annot/ad4", f"{name}.png"), big)
print("done")
