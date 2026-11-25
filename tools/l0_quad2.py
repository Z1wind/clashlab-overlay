# -*- coding: utf-8 -*-
import cv2, numpy as np, os
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
l0=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","ladder","zoom_L0.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
g=l0[80:630,155:1060]
for name,(x0,y0,x1,y1) in {
 "q_tl":(0,0,460,280),"q_tr":(445,0,905,280),
 "q_bl":(0,270,460,550),"q_br":(445,270,905,550)}.items():
    c=cv2.resize(g[y0:y1,x0:x1],None,fx=2,fy=2,interpolation=cv2.INTER_CUBIC)
    cv2.imencode(".png",c)[1].tofile(os.path.join(ROOT,"out","overlay",name+".png"))
print("ok")
