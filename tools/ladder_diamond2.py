# -*- coding: utf-8 -*-
"""ladder_diamond2.py — L0 中央建筑簇外廓（连通域 + 中央区域约束）。"""
import os, sys
import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LADDER = os.path.join(ROOT, "out", "overlay", "ladder")
L = sys.argv[1] if len(sys.argv) > 1 else "0"
p = os.path.join(LADDER, f"zoom_L{L}.png")
img = cv2.imdecode(np.fromfile(p, dtype=np.uint8), cv2.IMREAD_COLOR)
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
h, s, v = cv2.split(hsv)
# 草绿掩膜（较宽）
grass = ((h >= 32) & (h <= 100) & (s >= 15) & (s <= 130) & (v >= 60)).astype(np.uint8)
non = (1 - grass).astype(np.uint8)
# 去 UI：只剔顶/底/左/右条带，不夹中央
ui = np.ones_like(non)
ui[:55, :] = 0; ui[665:, :] = 0; ui[:, :120] = 0; ui[:, 1195:] = 0
m = (non & ui).astype(np.uint8)
m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
n, lab, stats, _ = cv2.connectedComponentsWithStats(m, 8)
# 取面积最大的若干簇并集
order = np.argsort(stats[1:, 4])[::-1][:6]
keep = np.zeros_like(m)
for k in order:
    keep[lab == k + 1] = 1
ys, xs = np.where(keep > 0)
print(f"L{L} 簇像素 {len(xs)}  left={xs.min()} right={xs.max()} top={ys.min()} bottom={ys.max()}")
Wd = xs.max() - xs.min(); Hd = ys.max() - ys.min()
print(f"Wd={Wd} Hd={Hd} W/H={Wd/Hd:.3f}  Wd/44={Wd/44:.2f}px")
vis = img.copy(); vis[keep == 0] = (0, 0, 0)
fp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ladder_out", f"L{L}_diamond2.png")
cv2.imencode(".png", vis)[1].tofile(fp)
print(fp)
