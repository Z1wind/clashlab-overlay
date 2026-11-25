# -*- coding: utf-8 -*-
"""象限像素标尺：每 20px 网格线 + 边缘坐标，供人工读建筑中心 px。"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from clashlab import vision
import cv2

img = vision.imread(os.path.join(ROOT, "out/snap/_source/home_village.png"))
quads = {
    "q1_tl": (120, 55, 680, 380),
    "q2_tr": (600, 55, 1190, 380),
    "q3_bl": (120, 340, 680, 670),
    "q4_br": (600, 340, 1190, 670),
}
for name, (x0, y0, x1, y1) in quads.items():
    base = img[y0:y1, x0:x1].copy()
    h, w = base.shape[:2]
    for x in range(0, w + 1, 20):
        cv2.line(base, (x, 0), (x, h), (200, 200, 255), 1)
        if x % 40 == 0:
            cv2.putText(base, str(x0 + x), (x + 2, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 1)
    for y in range(0, h + 1, 20):
        cv2.line(base, (0, y), (w, y), (200, 200, 255), 1)
        if y % 40 == 0:
            cv2.putText(base, str(y0 + y), (2, y + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 1)
    base = cv2.resize(base, None, fx=1.7, fy=1.7, interpolation=cv2.INTER_CUBIC)
    vision.imwrite(os.path.join(ROOT, f"out/snap/annot/{name}_ruler.png"), base)
    print(name, base.shape)
