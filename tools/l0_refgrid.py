# -*- coding: utf-8 -*-
# zoom_L0参考帧网格叠加+象限放大，目读菱形顶点
import cv2, numpy as np, os
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
ref=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","ladder","zoom_L0.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
c=ref[80:630,155:1105]
h,w=c.shape[:2]
g=c.copy()
for x in range(0,w,24):
    cv2.line(g,(x,0),(x,h),(0,0,255),1)
    if x%120==0: cv2.putText(g,str(x),(x+2,14),cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,0,255),1)
for y in range(0,h,24):
    cv2.line(g,(0,y),(w,y),(0,0,255),1)
    if y%120==0: cv2.putText(g,str(y),(2,y+12),cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,0,255),1)
cv2.imencode(".png",g)[1].tofile(os.path.join(ROOT,"out","overlay","l0new","ref_grid.png"))
for name,(x0,y0,x1,y1) in {"r_NW":(0,0,460,280),"r_NE":(445,0,905,280),"r_SW":(0,270,460,550),"r_SE":(445,270,905,550)}.items():
    q=cv2.resize(g[y0:y1,x0:x1],None,fx=2,fy=2,interpolation=cv2.INTER_CUBIC)
    cv2.imencode(".png",q)[1].tofile(os.path.join(ROOT,"out","overlay","l0new",name+".png"))
print("ref crop",w,h)
