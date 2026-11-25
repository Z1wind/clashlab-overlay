# -*- coding: utf-8 -*-
"""gold 标注辅助：给定 quad 与若干像素点，用 Calib.px_to_tile 打印 tile 坐标。

用法：
  python tools/px2tile.py --quad 698,100 955,371 669,592 334,341 --points 430,390 700,300
  也可 --auto 走 vision.detect_boundary。
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from clashlab import vision
from clashlab.geo import Calib, order_diamond


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", default="out/snap/_source/village.png")
    ap.add_argument("--quad", nargs=4)
    ap.add_argument("--auto", action="store_true")
    ap.add_argument("--points", nargs="+", required=True, help="x,y 列表")
    args = ap.parse_args()

    frame = vision.imread(args.image)
    if args.auto or not args.quad:
        info, _ = vision.analyze_frame(frame, focus="com.supercell.clashofclans")
        quad = np.array(info["boundary"]["quad"], dtype=np.float32)
        print("auto quad:", quad.tolist())
    else:
        pts = [tuple(float(v) for v in p.split(",")) for p in args.quad]
        quad = order_diamond(np.array(pts, dtype=np.float32))
    calib = Calib.from_quad(quad, n=44)
    for p in args.points:
        x, y = [float(v) for v in p.split(",")]
        gx, gy = calib.px_to_tile(x, y)
        inside = 0 <= gx <= 44 and 0 <= gy <= 44
        print(f"({x},{y}) -> tile ({gx:.2f},{gy:.2f}) inside={inside}")


if __name__ == "__main__":
    main()
