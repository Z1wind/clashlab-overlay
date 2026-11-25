# -*- coding: utf-8 -*-
"""裁家帧为 4 个重叠象限，放大供人工逐栋标注。"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from clashlab import vision
import cv2

img = vision.imread(os.path.join(ROOT, "out/snap/_source/home_village.png"))
os.makedirs(os.path.join(ROOT, "out/snap/annot"), exist_ok=True)
quads = {
    "q1_tl": (120, 55, 680, 380),
    "q2_tr": (600, 55, 1190, 380),
    "q3_bl": (120, 340, 680, 670),
    "q4_br": (600, 340, 1190, 670),
}
for name, (x0, y0, x1, y1) in quads.items():
    crop = img[y0:y1, x0:x1]
    crop = cv2.resize(crop, None, fx=1.7, fy=1.7, interpolation=cv2.INTER_CUBIC)
    vision.imwrite(os.path.join(ROOT, f"out/snap/annot/{name}.png"), crop)
    print(name, crop.shape)
