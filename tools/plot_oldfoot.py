# -*- coding: utf-8 -*-
"""把旧 gold 的 foot_px 直接画在原图上，核对脚点是否压在建筑上。"""
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from clashlab import vision
import cv2

g = json.load(open(os.path.join(ROOT, "out/snap/gold/home_village_gold.json"), encoding="utf-8"))
img = vision.imread(os.path.join(ROOT, "out/snap/_source/home_village.png"))
for b in g["buildings"]:
    x, y = b["foot_px"]
    cv2.circle(img, (int(x), int(y)), 8, (0, 255, 0), 2)
    cv2.putText(img, b["id"], (int(x)+8, int(y)-8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 2)
vision.imwrite(os.path.join(ROOT, "out/snap/annot/oldfoot.png"), img)
print("ok")
