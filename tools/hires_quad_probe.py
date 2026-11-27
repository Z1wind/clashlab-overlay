# -*- coding: utf-8 -*-
"""用亮草地掩膜 + 多边形近似找村庄菱形四角（1920x1080 家园截图）。"""
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
IMG = os.path.join(BASE, "out", "live", "hires", "coc_193842_6.png")
img = cv2.imdecode(np.fromfile(IMG, np.uint8), cv2.IMREAD_COLOR)
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
# 村庄草地：亮、偏黄绿；森林：暗
mask = cv2.inRange(hsv, (28, 30, 95), (95, 160, 255))
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8), iterations=2)
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8), iterations=1)
cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]
print("contours:", [int(cv2.contourArea(c)) for c in cnts])
best = None
for c in cnts:
    peri = cv2.arcLength(c, True)
    for eps in (0.02, 0.03, 0.05, 0.08):
        ap = cv2.approxPolyDP(c, eps * peri, True)
        if len(ap) == 4:
            area = cv2.contourArea(ap)
            if area > img.shape[0] * img.shape[1] * 0.10:
                best = (ap.reshape(4, 2).astype(np.float32), area)
                break
    if best: break
print("quad:", None if not best else best[0].tolist(), "area_ratio:", None if not best else round(best[1] / (img.shape[0]*img.shape[1]), 3))
vis = img.copy()
if best:
    cv2.polylines(vis, [best[0].astype(np.int32)], True, (0, 0, 255), 3)
cv2.imencode(".png", vis)[1].tofile(os.path.join(BASE, "out", "live", "hires_quad_probe.png"))
print("saved hires_quad_probe.png")
