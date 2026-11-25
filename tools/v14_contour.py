# -*- coding: utf-8 -*-
# v14_contour.py — 从 ov1 分割草地平台轮廓，拟合四角。新文件。
import os, cv2, numpy as np
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
EN = os.path.join(ROOT, "out", "overlay", "enemy")
im = cv2.imdecode(np.fromfile(os.path.join(EN, "b14_ov1.png"), dtype=np.uint8), cv2.IMREAD_COLOR)
hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
# 草地主色：浅黄绿
lo = np.array([25, 30, 90]); hi = np.array([85, 255, 255])
m = cv2.inRange(hsv, lo, hi)
m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((15,15),np.uint8))
m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((9,9),np.uint8))
cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
cnts = sorted(cnts, key=cv2.contourArea, reverse=True)
c = cnts[0]
hull = cv2.convexHull(c)
peri = cv2.arcLength(hull, True)
for eps in [0.005, 0.01, 0.015, 0.02]:
    ap = cv2.approxPolyDP(hull, eps*peri, True)
    print(f"eps {eps}: {len(ap)} pts")
    if len(ap) <= 8:
        pts = ap.reshape(-1,2)
        print(pts.tolist())
        break
vis = im.copy()
cv2.drawContours(vis, [hull], -1, (0,0,255), 2)
for p in pts:
    cv2.circle(vis, tuple(p), 6, (0,255,255), -1)
cv2.imencode(".png", vis)[1].tofile(os.path.join(EN, "b14_contour.png"))
