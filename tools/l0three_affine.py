# -*- coding: utf-8 -*-
# 仿射格网: 基向量沿墙向±36°, 24px/格; 中心/原点可调; 目检对齐
import cv2, numpy as np, os, sys
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
im=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","v6_l0_three_shot_base.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
H,W=im.shape[:2]
cx,cy=float(sys.argv[1]) if len(sys.argv)>1 else 470.0,float(sys.argv[2]) if len(sys.argv)>2 else 480.0
s=24.0
a1=np.radians(36.0); a2=np.radians(-36.0)
e1=np.array([np.cos(a1),np.sin(a1)])*s
e2=np.array([np.cos(a2),np.sin(a2)])*s
grid=im.copy()
for i in range(-30,31):
    p0=np.array([cx,cy])+i*e1-40*e2; p1=np.array([cx,cy])+i*e1+40*e2
    cv2.line(grid,tuple(p0.astype(int)),tuple(p1.astype(int)),(0,0,255),1)
for j in range(-30,31):
    p0=np.array([cx,cy])+j*e2-40*e1; p1=np.array([cx,cy])+j*e2+40*e1
    cv2.line(grid,tuple(p0.astype(int)),tuple(p1.astype(int)),(0,0,255),1)
cv2.imencode(".png",grid)[1].tofile(os.path.join(ROOT,"out","overlay","v6_l0_grid_aligned.png"))
print("ok",cx,cy)
