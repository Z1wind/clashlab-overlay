# -*- coding: utf-8 -*-
import cv2, numpy as np, os
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
l0=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","ladder","zoom_L0.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
g=l0[80:630,155:1060].copy()
# 中心带 x300-700 y150-420，20px网格，2x
sub=g[150:420,300:700]
for x in range(0,400,20):
    cv2.line(sub,(x,0),(x,270),(0,0,255),1)
    if x%40==0: cv2.putText(sub,str(300+x),(x+1,12),cv2.FONT_HERSHEY_SIMPLEX,0.35,(0,0,255),1)
for y in range(0,270,20):
    cv2.line(sub,(0,y),(400,y),(0,0,255),1)
    if y%40==0: cv2.putText(sub,str(150+y),(2,y+10),cv2.FONT_HERSHEY_SIMPLEX,0.35,(0,0,255),1)
sub=cv2.resize(sub,None,fx=2,fy=2,interpolation=cv2.INTER_CUBIC)
cv2.imencode(".png",sub)[1].tofile(os.path.join(ROOT,"out","overlay","l0_center2.png"))
print("ok")
