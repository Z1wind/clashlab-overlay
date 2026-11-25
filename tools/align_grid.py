# -*- coding: utf-8 -*-
"""坐标帧配准：仅用引擎 high/review 候选的 tile<->box 中心对应求 H（坐标登记，非识别），
画 44x44 网格叠加图供人工核对与逐栋标注。"""
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from clashlab import vision
import cv2
import numpy as np

d = json.load(open(os.path.join(ROOT, "out/snap/home_village/layout_candidates.json"), encoding="utf-8"))
anchors = []
for c in d["candidates"]:
    bx = c.get("box_px")
    if not bx:
        continue
    cx, cy = bx[0] + bx[2] / 2, bx[1] + bx[3] / 2
    anchors.append((c["tile"], (cx, cy)))
print("anchors", len(anchors))
src = np.array([t for t, _ in anchors], dtype=np.float32)
dst = np.array([p for _, p in anchors], dtype=np.float32)
H, mask = cv2.findHomography(src, dst, method=0)  # 最小二乘全点拟合，不做 RANSAC 剔点
print("H ok", H is not None)

img = vision.imread(os.path.join(ROOT, "out/snap/_source/home_village.png"))
# 画网格：tile(gx,gy) -> px
for gx in range(0, 45, 2):
    for gy in range(0, 45, 2):
        v = np.array([gx, gy, 1.0])
        p = H @ v
        x, y = int(p[0] / p[2]), int(p[1] / p[2])
        if 0 <= x < img.shape[1] and 0 <= y < img.shape[0]:
            cv2.circle(img, (x, y), 3, (0, 255, 0), -1)
# 网格线
for g in range(0, 45, 5):
    pts = []
    for gy in range(0, 45):
        p = H @ np.array([g, gy, 1.0]); pts.append((p[0]/p[2], p[1]/p[2]))
    for i in range(len(pts)-1):
        cv2.line(img, tuple(map(int, pts[i])), tuple(map(int, pts[i+1])), (0,255,255), 1)
    pts = []
    for gx in range(0, 45):
        p = H @ np.array([gx, g, 1.0]); pts.append((p[0]/p[2], p[1]/p[2]))
    for i in range(len(pts)-1):
        cv2.line(img, tuple(map(int, pts[i])), tuple(map(int, pts[i+1])), (255,0,255), 1)
vision.imwrite(os.path.join(ROOT, "out/snap/annot/grid_align.png"), img)
json.dump({"H": H.tolist(), "anchors": [[t, p] for t, p in anchors]},
          open(os.path.join(ROOT, "out/snap/annot/align_H.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print("saved")
