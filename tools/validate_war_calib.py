# -*- coding: utf-8 -*-
"""用 720p 已知手工 quad 校验战场标定算法（Hough/投影）。"""
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
import cv2, numpy as np
from tools.war_base_montage import wall_quad
IMG = os.path.join(BASE, "out", "live", "enemy_scout_live.png")
gt = np.float32([[640, 52], [1120, 352], [640, 652], [178, 352]])
img = cv2.imdecode(np.fromfile(IMG, np.uint8), cv2.IMREAD_COLOR)
print("img", img.shape)
quad, ang = wall_quad(img)
print("gt:", gt.tolist())
print("pred:", None if quad is None else np.round(quad, 1).tolist(), "angle", ang)
if quad is not None:
    # 与 GT 角点顺序对齐（左上起顺时针）后算平均误差
    print("mean abs err(px):", float(np.mean(np.abs(np.array(quad) - gt))))
