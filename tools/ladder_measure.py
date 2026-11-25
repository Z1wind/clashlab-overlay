# -*- coding: utf-8 -*-
"""ladder_measure.py — 档位帧离线直测辅助（纯离线，只读帧）。

用法：
  python ladder_measure.py grid <L> <x0> <y0> <x1> <y1> [scale]
      导出带原坐标网格的裁片到 tools/ladder_out/，供人工读数。
  python ladder_measure.py dist <x1> <y1> <x2> <y2>
      打印欧氏距离(px)。
  python ladder_measure.py run <L> <x0> <y0> <x1> <y1> <N>
      沿两点量长度 / N = px每格（墙段用）。
帧目录：out/overlay/ladder/zoom_L<L>.png（1280×720）。
"""
import os, sys
import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LADDER = os.path.join(ROOT, "out", "overlay", "ladder")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ladder_out")
os.makedirs(OUT, exist_ok=True)


def load(L):
    p = os.path.join(LADDER, f"zoom_L{L}.png")
    return cv2.imdecode(np.fromfile(p, dtype=np.uint8), cv2.IMREAD_COLOR)


def cmd_grid(L, x0, y0, x1, y1, scale=2):
    img = load(L)
    crop = img[y0:y1, x0:x1].copy()
    h, w = crop.shape[:2]
    big = cv2.resize(crop, (w * scale, h * scale), interpolation=cv2.INTER_NEAREST)
    # 每 25 原像素浅灰细线；每 50 原像素红粗线+坐标标签
    for x in range(0, w + 1, 25):
        xv = x * scale
        strong = (x % 50 == 0)
        cv2.line(big, (xv, 0), (xv, h * scale), (0, 0, 255) if strong else (180, 180, 180),
                 2 if strong else 1)
        if strong:
            cv2.putText(big, str(x0 + x), (xv + 3, 18), cv2.FONT_HERSHEY_SIMPLEX,
                        0.55, (0, 0, 255), 2)
    for y in range(0, h + 1, 25):
        yv = y * scale
        strong = (y % 50 == 0)
        cv2.line(big, (0, yv), (w * scale, yv), (0, 0, 255) if strong else (180, 180, 180),
                 2 if strong else 1)
        if strong:
            cv2.putText(big, str(y0 + y), (3, yv + 16), cv2.FONT_HERSHEY_SIMPLEX,
                        0.55, (0, 0, 255), 2)
    fp = os.path.join(OUT, f"L{L}_grid_{x0}_{y0}_{x1}_{y1}.png")
    ok, buf = cv2.imencode(".png", big)
    buf.tofile(fp)
    print(fp)


def cmd_dist(x1, y1, x2, y2):
    d = float(np.hypot(x2 - x1, y2 - y1))
    print(f"dist = {d:.2f} px  (dx={x2-x1}, dy={y2-y1})")
    return d


def cmd_run(L, x0, y0, x1, y1, N):
    d = float(np.hypot(x1 - x0, y1 - y0))
    print(f"长度={d:.2f}px / {N}格 = {d / N:.3f} px/格")
    return d / N


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "grid":
        cmd_grid(a[1], *map(int, a[2:6]), int(a[6]) if len(a) > 6 else 2)
    elif a[0] == "dist":
        cmd_dist(*map(int, a[1:5]))
    elif a[0] == "run":
        cmd_run(a[1], *map(int, a[2:7]))
