# -*- coding: utf-8 -*-
"""画 v2 gold foot_px 复核：绿=库内类型，橙=无类型/墙外，蓝=墙。"""
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from clashlab import vision
import cv2

g = json.load(open(os.path.join(ROOT, "out/snap/gold/home_village_gold.json"), encoding="utf-8"))
LIB = {"archer-tower","cannon","mortar","x-bow","hidden-tesla","air-defense","wizard-tower",
       "air-sweeper","bomb-tower","eagle-artillery","firespitter","inferno-tower",
       "monolith","multi-archer-tower","scattershot","spell-tower","town-hall"}
img = vision.imread(os.path.join(ROOT, "out/snap/_source/home_village.png"))
for b in g["buildings"]:
    x, y = b["foot_px"]
    if b["type"] == "wall":
        col = (255, 0, 0)
    elif b["type"] in LIB:
        col = (0, 255, 0)
    else:
        col = (0, 165, 255)
    cv2.circle(img, (int(x), int(y)), 9, col, 2)
    cv2.putText(img, b["id"], (int(x)+10, int(y)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0,0,0), 2)
vision.imwrite(os.path.join(ROOT, "out/snap/annot/v2foot.png"), img)
print("ok")
