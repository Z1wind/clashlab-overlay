# -*- coding: utf-8 -*-
"""方案 A：拍干净截图并切四象限放大（带 50px 网格与坐标标注），供人工读图标注。"""
import sys, time, os
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import al_drive as d

BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(BASE, "out", "overlay", "_auto_label")
os.makedirs(os.path.join(OUT, "views"), exist_ok=True)

d.tap(300, 650, "deselect")
time.sleep(1.0)
img = d.shot(os.path.join(OUT, "views", "full.png"))
print("full", img.shape)

# 四象限，各放大 2 倍并画网格（网格步长 25px 原图 = 50px 放大）
quads = {"q1": (0, 0, 660, 380), "q2": (620, 0, 1280, 380),
         "q3": (0, 340, 660, 720), "q4": (620, 340, 1280, 720)}
for name, (x0, y0, x1, y1) in quads.items():
    crop = img[y0:y1, x0:x1]
    big = cv2.resize(crop, ((x1 - x0) * 2, (y1 - y0) * 2), interpolation=cv2.INTER_CUBIC)
    vis = big.copy()
    for gx in range(0, big.shape[1], 50):
        ox = x0 + gx // 2
        cv2.line(vis, (gx, 0), (gx, big.shape[0]), (0, 255, 255), 1)
        if (ox % 100) == 0:
            cv2.putText(vis, str(ox), (gx + 2, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)
    for gy in range(0, big.shape[0], 50):
        oy = y0 + gy // 2
        cv2.line(vis, (0, gy), (big.shape[1], gy), (0, 255, 255), 1)
        if (oy % 100) == 0:
            cv2.putText(vis, str(oy), (2, gy + 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)
    cv2.imencode(".png", vis)[1].tofile(os.path.join(OUT, "views", name + ".png"))
    print("wrote", name, vis.shape)
