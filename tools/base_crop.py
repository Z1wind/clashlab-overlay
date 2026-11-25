# -*- coding: utf-8 -*-
"""base_crop.py — 任意大图带坐标网格裁片导出（纯离线，供人工读点）。

用法：python base_crop.py <img> <x0> <y0> <x1> <y1> [scale]
输出 tools/base_out/<name>_grid.png，红粗线=50px，灰细线=25px。
"""
import os, sys
import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "base_out")
os.makedirs(OUT, exist_ok=True)

img = cv2.imdecode(np.fromfile(sys.argv[1], dtype=np.uint8), cv2.IMREAD_COLOR)
x0, y0, x1, y1 = map(int, sys.argv[2:6])
scale = int(sys.argv[6]) if len(sys.argv) > 6 else 2
crop = img[y0:y1, x0:x1].copy()
h, w = crop.shape[:2]
big = cv2.resize(crop, (w * scale, h * scale), interpolation=cv2.INTER_NEAREST)
for x in range(0, w + 1, 25):
    xv = x * scale
    strong = x % 50 == 0
    cv2.line(big, (xv, 0), (xv, h * scale), (0, 0, 255) if strong else (180, 180, 180), 2 if strong else 1)
    if strong:
        cv2.putText(big, str(x0 + x), (xv + 3, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)
for y in range(0, h + 1, 25):
    yv = y * scale
    strong = y % 50 == 0
    cv2.line(big, (0, yv), (w * scale, yv), (0, 0, 255) if strong else (180, 180, 180), 2 if strong else 1)
    if strong:
        cv2.putText(big, str(y0 + y), (3, yv + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)
name = os.path.splitext(os.path.basename(sys.argv[1]))[0]
fp = os.path.join(OUT, f"{name}_{x0}_{y0}_{x1}_{y1}.png")
cv2.imencode(".png", big)[1].tofile(fp)
print(fp)
