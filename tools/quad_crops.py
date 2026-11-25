# -*- coding: utf-8 -*-
"""切 home_village.png 为四块，供人工数防空塔等单类目标。"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from clashlab.vision import imread, imwrite

img = imread(os.path.join(ROOT, "out/snap/_source/home_village.png"))
h, w = img.shape[:2]
OUT = os.path.join(ROOT, "out/snap/annot/quad")
os.makedirs(OUT, exist_ok=True)
# 4 块，互相重叠 40px
for name, (x0, y0, x1, y1) in {
    "q_tl": (0, 0, w // 2 + 40, h // 2 + 40),
    "q_tr": (w // 2 - 40, 0, w, h // 2 + 40),
    "q_bl": (0, h // 2 - 40, w // 2 + 40, h),
    "q_br": (w // 2 - 40, h // 2 - 40, w, h),
}.items():
    imwrite(os.path.join(OUT, f"{name}.png"), img[y0:y1, x0:x1])
    print(name, (x0, y0, x1, y1))
