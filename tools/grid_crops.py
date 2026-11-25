# -*- coding: utf-8 -*-
"""裁 grid_check.png 锚点区域，供目视核对引擎格线是否压在菱形骨架/墙角上。"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from clashlab.vision import imread, imwrite

SRC = os.path.join(ROOT, "out/check_verify/home_village/grid_check.png")
OUT = os.path.join(ROOT, "out/snap/annot/grid_crops")
os.makedirs(OUT, exist_ok=True)

# (名称, 中心px, 半边长)
CROPS = {
    "th_center": (630, 365, 110),
    "top_wall_corner": (560, 95, 100),
    "right_mid": (1010, 360, 100),
    "left_mid": (250, 360, 100),
    "bottom_center": (620, 610, 100),
    "top_right": (960, 200, 100),
    "bottom_left": (300, 560, 100),
    "center_ring": (630, 480, 100),
}
img = imread(SRC)
h, w = img.shape[:2]
for name, (cx, cy, r) in CROPS.items():
    x0, y0 = max(0, cx - r), max(0, cy - r)
    x1, y1 = min(w, cx + r), min(h, cy + r)
    imwrite(os.path.join(OUT, f"{name}.png"), img[y0:y1, x0:x1])
    print(name, (x0, y0, x1, y1))
