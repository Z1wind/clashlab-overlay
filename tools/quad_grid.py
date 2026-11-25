# -*- coding: utf-8 -*-
"""按旧 H 在 4 个象限上叠加网格点与格号，放大供人工读格标注。"""
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from clashlab import vision
from clashlab.geo import Calib
import cv2

g = json.load(open(os.path.join(ROOT, "out/snap/gold/home_village_gold.json"), encoding="utf-8"))
calib = Calib.from_dict(g["calib"])
img = vision.imread(os.path.join(ROOT, "out/snap/_source/home_village.png"))

quads = {
    "q1_tl": (120, 55, 680, 380),
    "q2_tr": (600, 55, 1190, 380),
    "q3_bl": (120, 340, 680, 670),
    "q4_br": (600, 340, 1190, 670),
}
for name, (x0, y0, x1, y1) in quads.items():
    base = img[y0:y1, x0:x1].copy()
    for gx in range(45):
        for gy in range(45):
            x, y = calib.tile_to_px(gx, gy)
            if x0 <= x < x1 and y0 <= y < y1:
                cx, cy = int(x - x0), int(y - y0)
                cv2.circle(base, (cx, cy), 3, (0, 220, 0), -1)
                cv2.putText(base, f"{gx},{gy}", (cx + 4, cy - 4),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.28, (0, 0, 0), 1, cv2.LINE_AA)
    base = cv2.resize(base, None, fx=1.7, fy=1.7, interpolation=cv2.INTER_CUBIC)
    vision.imwrite(os.path.join(ROOT, f"out/snap/annot/{name}_grid.png"), base)
    print(name, base.shape)
