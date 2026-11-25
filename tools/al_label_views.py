# -*- coding: utf-8 -*-
"""用已有的干净全基地截图（zoom1.png）切四象限 + 网格，供人工读图标注。"""
import os, sys
import numpy as np, cv2
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(BASE, "out", "overlay", "_auto_label")
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(OUT, "zoom1.png")
DST = os.path.join(OUT, "views")
os.makedirs(DST, exist_ok=True)
img = cv2.imdecode(np.fromfile(SRC, np.uint8), cv2.IMREAD_COLOR)
print("src", SRC, img.shape)
cv2.imencode(".png", img)[1].tofile(os.path.join(DST, "label_src.png"))
quads = {"m1": (110, 40, 690, 400), "m2": (620, 40, 1200, 400),
         "m3": (110, 360, 690, 700), "m4": (620, 360, 1200, 700)}
for name, (x0, y0, x1, y1) in quads.items():
    crop = img[y0:y1, x0:x1]
    big = cv2.resize(crop, ((x1 - x0) * 2, (y1 - y0) * 2), interpolation=cv2.INTER_CUBIC)
    vis = big.copy()
    for gx in range(0, big.shape[1], 40):
        ox = x0 + gx // 2
        cv2.line(vis, (gx, 0), (gx, big.shape[0]), (0, 255, 255), 1)
        if (ox % 80) == 0:
            cv2.putText(vis, str(ox), (gx + 1, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 0, 255), 1)
    for gy in range(0, big.shape[0], 40):
        oy = y0 + gy // 2
        cv2.line(vis, (0, gy), (big.shape[1], gy), (0, 255, 255), 1)
        if (oy % 80) == 0:
            cv2.putText(vis, str(oy), (1, gy + 13), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 0, 255), 1)
    cv2.imencode(".png", vis)[1].tofile(os.path.join(DST, name + ".png"))
    print("wrote", name, vis.shape)
