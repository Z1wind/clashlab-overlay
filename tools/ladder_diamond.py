# -*- coding: utf-8 -*-
"""ladder_diamond.py — L0 全阵菱形外廓掩膜极值测量（纯离线）。

排除 UI 区（左面板 x<130、右导轨 x>1180、顶栏 y<60、底栏 y>660）；
非草绿掩膜 → 左右/上下极值；tile_px = 横宽/44（名义 44 格横对角线）。
"""
import os, sys
import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LADDER = os.path.join(ROOT, "out", "overlay", "ladder")


def load(L):
    p = os.path.join(LADDER, f"zoom_L{L}.png")
    return cv2.imdecode(np.fromfile(p, dtype=np.uint8), cv2.IMREAD_COLOR)


img = load(sys.argv[1] if len(sys.argv) > 1 else "0")
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
h, s, v = cv2.split(hsv)
# 草绿：色相 35-95、中低饱和；非草=其余
grass = ((h >= 35) & (h <= 95) & (s >= 20) & (s <= 120)).astype(np.uint8)
non = (1 - grass).astype(np.uint8)
# UI 排除带
ui = np.zeros_like(non)
ui[60:660, 130:1180] = 1
m = non & ui
ys, xs = np.where(m > 0)
print(f"非草像素 {len(xs)}")
print(f"left={xs.min()} right={xs.max()} top={ys.min()} bottom={ys.max()}")
Wd = xs.max() - xs.min()
Hd = ys.max() - ys.min()
print(f"横宽 Wd={Wd}px  竖高 Hd={Hd}px  W/H={Wd/Hd:.3f}")
print(f"tile_px = Wd/44 = {Wd/44:.2f}px  (名义44格横对角线)")
# 输出掩膜可视
vis = img.copy()
vis[m == 0] = (0, 0, 0)
fp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ladder_out",
                  f"L{sys.argv[1] if len(sys.argv)>1 else 0}_diamond.png")
cv2.imencode(".png", vis)[1].tofile(fp)
print(fp)
