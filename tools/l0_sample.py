# -*- coding: utf-8 -*-
import cv2, numpy as np, os
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
l0=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","ladder","zoom_L0.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
g=l0[80:630,155:1060]
hsv=cv2.cvtColor(g,cv2.COLOR_BGR2HSV)
for name,(x,y) in {"lawn1":(360,250),"lawn2":(620,150),"lawn3":(210,400),"lawn4":(700,420),
                   "forest1":(860,120),"forest2":(900,330),"river":(60,520),"stone":(450,300)}.items():
    print(name,"BGR",g[y,x],"HSV",hsv[y,x])
