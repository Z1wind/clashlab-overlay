# -*- coding: utf-8 -*-
# 城墙段专用裁切：NE 上墙 + SE 右墙，放大2x，供数步长
import cv2, numpy as np, os
OUT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay"
img = cv2.imdecode(np.fromfile(os.path.join(OUT, "v6_zoom_max_raw.png"), dtype=np.uint8), cv2.IMREAD_COLOR)
# NE 上墙 (原坐标)
c1 = img[0:280, 380:980]
cv2.imencode(".png", cv2.resize(c1, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC))[1].tofile(os.path.join(OUT, "v6_wall_ne.png"))
# 右侧竖直向墙
c2 = img[120:620, 620:1080]
cv2.imencode(".png", cv2.resize(c2, None, fx=1.8, fy=1.8, interpolation=cv2.INTER_CUBIC))[1].tofile(os.path.join(OUT, "v6_wall_se.png"))
print("ok")
