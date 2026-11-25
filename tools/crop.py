# -*- coding: utf-8 -*-
"""gold 标注辅助：切矩形放大图并画像素标尺，供人工读点。

用法：python tools/crop.py --image out/snap/_source/village.png --box x1,y1,x2,y2 --out crop.png --scale 2
"""
import argparse
import os
import sys

import cv2

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from clashlab import vision


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--box", required=True, help="x1,y1,x2,y2（原图像素）")
    ap.add_argument("--out", required=True)
    ap.add_argument("--scale", type=float, default=2.0)
    args = ap.parse_args()

    frame = vision.imread(args.image)
    x1, y1, x2, y2 = [int(v) for v in args.box.split(",")]
    crop = frame[y1:y2, x1:x2].copy()
    h, w = crop.shape[:2]
    crop = cv2.resize(crop, (int(w * args.scale), int(h * args.scale)), interpolation=cv2.INTER_CUBIC)
    # 标尺：每 20 原图像素一刻度，标原坐标
    for gx in range((x1 // 20) * 20, x2, 20):
        sx = int((gx - x1) * args.scale)
        cv2.line(crop, (sx, 0), (sx, 12), (0, 255, 0), 1)
        cv2.putText(crop, str(gx), (sx + 2, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 0), 1)
    for gy in range((y1 // 20) * 20, y2, 20):
        sy = int((gy - y1) * args.scale)
        cv2.line(crop, (0, sy), (12, sy), (255, 0, 0), 1)
        cv2.putText(crop, str(gy), (2, sy + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 0, 0), 1)
    vision.imwrite(args.out, crop)
    print("wrote", args.out)


if __name__ == "__main__":
    main()
