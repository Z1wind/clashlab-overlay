# -*- coding: utf-8 -*-
# v10_edges.py — 离线：Canny+Hough 提取外墙直线段，聚类，出调试图。
import cv2, numpy as np, os, sys
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
RAW = os.path.join(ROOT, "out", "overlay", "full", "raw")
im = cv2.imdecode(np.fromfile(os.path.join(RAW, "wheel_test.png"), dtype=np.uint8), cv2.IMREAD_COLOR)
# 内容裁口
x1, y1, x2, y2 = 150, 75, 1015, 612
c = im[y1:y2, x1:x2]
g = cv2.cvtColor(c, cv2.COLOR_BGR2GRAY)
edges = cv2.Canny(g, 60, 160, apertureSize=3)
lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=60, minLineLength=60, maxLineGap=12)
vis = c.copy()
segs = []
if lines is not None:
    for l in lines.reshape(-1, 4):
        xa, ya, xb, yb = int(l[0]), int(l[1]), int(l[2]), int(l[3])
        length = np.hypot(xb - xa, yb - ya)
        ang = np.degrees(np.arctan2(yb - ya, xb - xa))
        segs.append((xa, ya, xb, yb, length, ang))
        cv2.line(vis, (xa, ya), (xb, yb), (0, 0, 255), 1)
print("n_lines=", len(segs))
# 角度直方图
for s in sorted(segs, key=lambda s: -s[4])[:40]:
    print(f"({s[0]},{s[1]})-({s[2]},{s[3]}) len={s[4]:.0f} ang={s[5]:.1f}")
cv2.imencode(".png", vis)[1].tofile(os.path.join(RAW, "edges_debug.png"))
cv2.imencode(".png", edges)[1].tofile(os.path.join(RAW, "edges_mask.png"))
print("saved")
