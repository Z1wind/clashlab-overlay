# -*- coding: utf-8 -*-
"""人眼全图 quad 网格核对：四角取外墙骨架顶点。"""
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from clashlab import vision
from clashlab.geo import Calib
import cv2
import numpy as np

# 人眼外墙顶点（上/右/下/左）
QUAD = [[520, 40], [1180, 360], [600, 730], [90, 360]]
calib = Calib.from_quad(QUAD, n=44)
img = vision.imread(os.path.join(ROOT, "out/snap/_source/home_village.png"))
for gx in range(0, 45, 1):
    for gy in range(0, 45, 1):
        x, y = calib.tile_to_px(gx, gy)
        xi, yi = int(round(x)), int(round(y))
        if 0 <= xi < img.shape[1] and 0 <= yi < img.shape[0]:
            cv2.circle(img, (xi, yi), 2, (0, 220, 0), -1)
for g in range(0, 45, 5):
    a = [calib.tile_to_px(g, gy) for gy in range(45)]
    for i in range(44):
        cv2.line(img, tuple(map(int, a[i])), tuple(map(int, a[i+1])), (0, 200, 255), 1)
    b = [calib.tile_to_px(gx, g) for gx in range(45)]
    for i in range(44):
        cv2.line(img, tuple(map(int, b[i])), tuple(map(int, b[i+1])), (255, 0, 255), 1)
for gx in range(0, 45, 10):
    for gy in range(0, 45, 10):
        x, y = calib.tile_to_px(gx, gy)
        cv2.putText(img, f"{gx},{gy}", (int(x)+3, int(y)-3), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0,0,0), 1)
vision.imwrite(os.path.join(ROOT, "out/snap/annot/grid_human.png"), img)
json.dump({"quad": QUAD, "H": calib.H.tolist()},
          open(os.path.join(ROOT, "out/snap/annot/human_H.json"), "w", encoding="utf-8"), indent=2)
print("reproj", calib.reproj_error())
