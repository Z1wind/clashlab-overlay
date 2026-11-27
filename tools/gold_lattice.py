# -*- coding: utf-8 -*-
"""用城墙金顶（金色小点）拟合 44x44 网格：检测金顶中心 → 估计晶格基向量 → 最小二乘定原点。"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
IMG = BASE + r"\out\live\war1080\base_01_215536.png"
img = cv2.imdecode(np.fromfile(IMG, np.uint8), cv2.IMREAD_COLOR)
h, w = img.shape[:2]
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
# 金色：H 15-35, S>140, V>150
mask = cv2.inRange(hsv, (15, 140, 150), (35, 255, 255))
# 排除 UI
mask[:90, :] = 0; mask[:, :340] = 0; mask[:, 1700:] = 0; mask[900:, :] = 0
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
num, lab, stats, cents = cv2.connectedComponentsWithStats(mask, 8)
pts = []
for i in range(1, num):
    x, y, ww, hh, area = stats[i]
    if 6 <= area <= 120 and 0.4 <= ww / max(1, hh) <= 2.5:
        pts.append(cents[i])
pts = np.array(pts, np.float32)
print("gold caps:", len(pts))
if len(pts) > 20:
    # 近邻差分统计
    from scipy.spatial import cKDTree  # 可能没有 scipy
    print("has scipy")
