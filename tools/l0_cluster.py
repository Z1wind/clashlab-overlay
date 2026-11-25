# -*- coding: utf-8 -*-
# 对 L0 裁片做颜色 kmeans，打印主色簇 HSV/BGR，找草坪簇
import cv2, numpy as np, os
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
l0=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","ladder","zoom_L0.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
g=l0[80:630,155:1060]
hsv=cv2.cvtColor(g,cv2.COLOR_BGR2HSV)
Z=hsv.reshape(-1,3).astype(np.float32)
_,lab,cent=cv2.kmeans(Z,8,None,(cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER,20,1.0),3,cv2.KMEANS_PP_CENTERS)
counts=np.bincount(lab.flatten())
for c,n in sorted(zip(cent,counts),key=lambda t:-t[1]):
    print(f"HSV=({c[0]:.0f},{c[1]:.0f},{c[2]:.0f}) n={n}")
