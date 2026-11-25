# -*- coding: utf-8 -*-
# 仿射格网：方向取Hough A(+35°)/B(−34°)，24px/格，中心可调；覆盖村庄
import cv2, numpy as np, os, json
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
base=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","v6_l0_two_shot_base.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
H,W=base.shape[:2]
# 可调参数
cx,cy=470,395
angA=np.radians(0.0); angB=np.radians(90.0)
s=24.0
e1=np.array([np.cos(angA),np.sin(angA)])*s
e2=np.array([np.cos(angB),np.sin(angB)])*s
grid=base.copy()
# 画 i/j 格线（范围覆盖画布）
for i in range(-22,23):
    p0=np.array([cx,cy])+i*e1-30*e2; p1=np.array([cx,cy])+i*e1+30*e2
    cv2.line(grid,tuple(p0.astype(int)),tuple(p1.astype(int)),(0,0,255),1)
for j in range(-22,23):
    p0=np.array([cx,cy])+j*e2-30*e1; p1=np.array([cx,cy])+j*e2+30*e1
    cv2.line(grid,tuple(p0.astype(int)),tuple(p1.astype(int)),(0,0,255),1)
cv2.imencode(".png",grid)[1].tofile(os.path.join(ROOT,"out","overlay","v6_l0_grid_aligned.png"))
print("ok",cx,cy)
