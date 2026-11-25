# -*- coding: utf-8 -*-
"""gold 标注辅助：用 Calib.from_quad 把网格画到截图上，输出叠加图供人工核对。

用法（项目根目录下）：
  python tools/grid_overlay.py --image out/snap/_source/village.png --out out/snap/_source/grid_auto.png
  python tools/grid_overlay.py --image ... --quad 698,100 955,371 669,592 334,341 --out grid_manual.png

quad 顺序：上、右、下、左（order_diamond 已归一，这里直接喂四点也行）。
本脚本只做可视化，坐标换算一律走 clashlab.geo.Calib。
"""
import argparse
import json
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from clashlab import vision
from clashlab.geo import Calib, order_diamond


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--quad", nargs=4, help="x,y x,y x,y x,y，缺省走 vision.detect_boundary")
    ap.add_argument("--out", required=True)
    ap.add_argument("--step", type=int, default=2)
    args = ap.parse_args()

    frame = vision.imread(args.image)
    if frame is None:
        raise SystemExit(f"读不到 {args.image}")

    if args.quad:
        pts = [tuple(float(v) for v in p.split(",")) for p in args.quad]
        quad = order_diamond(np.array(pts, dtype=np.float32))
    else:
        info, calib = vision.analyze_frame(frame, focus="com.supercell.clashofclans")
        quad = np.array(info["boundary"]["quad"], dtype=np.float32)
        print(json.dumps({"auto_boundary": info["boundary"], "reproj": info["reproj"]}, ensure_ascii=False))

    calib = Calib.from_quad(quad, n=44)
    img = frame.copy()
    # 网格线
    for g in range(0, 45, args.step):
        p0 = calib.tile_to_px(g, 0)
        p1 = calib.tile_to_px(g, 44)
        p2 = calib.tile_to_px(0, g)
        p3 = calib.tile_to_px(44, g)
        cv2.line(img, (int(p0[0]), int(p0[1])), (int(p1[0]), int(p1[1])), (0, 255, 0), 1)
        cv2.line(img, (int(p2[0]), int(p2[1])), (int(p3[0]), int(p3[1])), (255, 0, 0), 1)
    # 四角 + 每5格标注
    for i, (x, y) in enumerate(quad):
        cv2.circle(img, (int(x), int(y)), 8, (0, 0, 255), -1)
        cv2.putText(img, f"Q{i}", (int(x) + 10, int(y)), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    for gx in range(0, 45, 5):
        for gy in range(0, 45, 5):
            px, py = calib.tile_to_px(gx, gy)
            cv2.putText(img, f"{gx},{gy}", (int(px) - 18, int(py) + 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 0), 1)
    vision.imwrite(args.out, img)
    print("wrote", args.out)


if __name__ == "__main__":
    main()
