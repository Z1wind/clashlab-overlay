# -*- coding: utf-8 -*-
# L0 帧裁游戏区 +24px网格叠加，供目读菱形四角
import cv2, numpy as np, os
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
l0=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","ladder","zoom_L0.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
g=l0[80:630,155:1060].copy()
h,w=g.shape[:2]
for x in range(0,w,24): cv2.line(g,(x,0),(x,h),(0,0,255),1)
for y in range(0,h,24): cv2.line(g,(0,y),(w,y),(0,0,255),1)
cv2.imencode(".png",g)[1].tofile(os.path.join(ROOT,"out","overlay","l0_grid.png"))
# 采样：平台中部(450,300) 与 森林(800,80) 与 河边(120,500)
for name,(x,y) in {"mid":(450,300),"forest":(820,90),"river":(130,500),"lawn_edge":(300,470)}.items():
    print(name,g[y,x])
