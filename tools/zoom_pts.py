# -*- coding: utf-8 -*-
"""对存疑/已标条目逐个出 3x 放大裁剪，供类型复核。"""
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from clashlab import vision
import cv2

img = vision.imread(os.path.join(ROOT, "out/snap/_source/home_village.png"))
g = json.load(open(os.path.join(ROOT, "out/snap/gold/home_village_gold.json"), encoding="utf-8"))
os.makedirs(os.path.join(ROOT, "out/snap/annot/zoom"), exist_ok=True)
for b in g["buildings"]:
    cx, cy = b["foot_px"]
    x0, y0 = max(0, cx-45), max(0, cy-45)
    x1, y1 = min(img.shape[1], cx+45), min(img.shape[0], cy+45)
    crop = img[y0:y1, x0:x1]
    crop = cv2.resize(crop, None, fx=3.0, fy=3.0, interpolation=cv2.INTER_CUBIC)
    cv2.putText(crop, f'{b["id"]} {b["type"]}', (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)
    vision.imwrite(os.path.join(ROOT, f"out/snap/annot/zoom/{b['id']}.png"), crop)
print("done", len(g["buildings"]))
