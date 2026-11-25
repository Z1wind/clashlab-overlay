# -*- coding: utf-8 -*-
"""把 gold 脚点画到源图供人工复核（只读）。用法:
python tools/draw_gold.py --gold out/snap/gold/home_village_gold.json --out out/snap/_source/home_markers.png
"""
import argparse
import json
import os
import sys

import cv2

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from clashlab import vision

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    with open(os.path.join(ROOT, args.gold), encoding="utf-8") as f:
        gold = json.load(f)
    img = vision.imread(os.path.join(ROOT, gold["source_image"]))
    for b in gold["buildings"]:
        x, y = b["foot_px"]
        color = (0, 255, 0) if b["type"] else (0, 165, 255)
        cv2.circle(img, (x, y), 7, color, -1)
        cv2.putText(img, b["id"], (x + 9, y - 9), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 2)
    vision.imwrite(os.path.join(ROOT, args.out), img)
    print("wrote", args.out)


if __name__ == "__main__":
    main()
