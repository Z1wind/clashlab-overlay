# -*- coding: utf-8 -*-
"""用城墙像素极值点求村庄菱形四角（墙=白/橙，极值≈44格网格四角）。"""
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
IMG = os.path.join(BASE, "out", "live", "hires", "coc_193842_6.png")
img = cv2.imdecode(np.fromfile(IMG, np.uint8), cv2.IMREAD_COLOR)
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
h, w = img.shape[:2]
# 城墙：白/米白（低饱和高亮）或橙盖（H 12-30）
white = cv2.inRange(hsv, (0, 0, 150), (180, 60, 255))
orange = cv2.inRange(hsv, (8, 100, 120), (32, 255, 255))
mask = cv2.bitwise_or(white, orange)
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
# 排除 UI 区域
mask[:70, :] = 0          # 顶部状态栏
mask[:, :330] = 0         # 左侧面板
mask[:, 1700:] = 0        # 右侧面板
mask[900:, :] = 0         # 底部按钮
ys, xs = np.nonzero(mask)
print("mask px:", len(xs))
if len(xs) < 1000:
    raise SystemExit("mask too small")
def pick(score_idx):
    i = int(score_idx)
    return [int(xs[i]), int(ys[i])]
left = pick(np.argmin(xs)); right = pick(np.argmax(xs))
top = pick(np.argmin(ys)); bottom = pick(np.argmax(ys))
quad = np.float32([left, top, right, bottom])
print("quad L,T,R,B:", [list(map(int, q)) for q in quad])
# 面积检验
vis = img.copy()
cv2.polylines(vis, [quad.astype(np.int32)], True, (0, 0, 255), 3)
for p, name in zip(quad, "LTRB"):
    cv2.circle(vis, (int(p[0]), int(p[1])), 9, (0, 0, 255), -1)
    cv2.putText(vis, name, (int(p[0])+12, int(p[1])+12), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,0,255), 2)
cv2.imencode(".png", vis)[1].tofile(os.path.join(BASE, "out", "live", "hires_wall_quad.png"))
np.save(os.path.join(BASE, "out", "live", "hires_wall_quad.npy"), quad)
print("saved hires_wall_quad.png")
