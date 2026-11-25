# -*- coding: utf-8 -*-
# L0 裁片四分位放大 + 每24px刻度标注，供目读菱形顶点
import cv2, numpy as np, os
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
l0=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","ladder","zoom_L0.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
g=l0[80:630,155:1060].copy()
h,w=g.shape[:2]
for x in range(0,w,24):
    cv2.line(g,(x,0),(x,h),(0,0,255),1)
    if x%120==0: cv2.putText(g,str(x),(x+2,14),cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,0,255),1)
for y in range(0,h,24):
    cv2.line(g,(0,y),(w,y),(0,0,255),1)
    if y%120==0: cv2.putText(g,str(y),(2,y+12),cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,0,255),1)
# 上下两半 2x
for name,(y0,y1) in {"q_top":(0,300),"q_bot":(250,550)}.items():
    c=cv2.resize(g[y0:y1],None,fx=2,fy=2,interpolation=cv2.INTER_CUBIC)
    cv2.imencode(".png",c)[1].tofile(os.path.join(ROOT,"out","overlay",name+".png"))
print("done")
