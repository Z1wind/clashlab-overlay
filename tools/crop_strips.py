# -*- coding: utf-8 -*-
"""中央带与顶/底条带像素标尺裁切。"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from clashlab import vision
import cv2

img = vision.imread(os.path.join(ROOT, "out/snap/_source/home_village.png"))
strips = {
    "center": (500, 290, 760, 480),
    "topstrip": (120, 55, 1180, 150),
    "bottomstrip": (120, 600, 1180, 700),
}
for name, (x0, y0, x1, y1) in strips.items():
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
    scale = 1.7 if name != "topstrip" else 1.4
    base = cv2.resize(base, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    vision.imwrite(os.path.join(ROOT, f"out/snap/annot/{name}_ruler.png"), base)
    print(name, base.shape)
