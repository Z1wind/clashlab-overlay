# -*- coding: utf-8 -*-
import cv2, numpy as np, os, sys
D=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\ladder"
img=cv2.imdecode(np.fromfile(os.path.join(D,sys.argv[1]),dtype=np.uint8),cv2.IMREAD_COLOR)
x1,y1,x2,y2=map(int,sys.argv[2:6]); sc=float(sys.argv[6])
c=img[y1:y2,x1:x2]
# 每20px淡网格，坐标只标左/上边，大字号
for x in range(0,x2-x1,20):
    cv2.line(c,(x,0),(x,y2-y1),(0,200,0),1)
    cv2.putText(c,str(x1+x),(x+2,24),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,255,0),2)
for y in range(0,y2-y1,20):
    cv2.line(c,(0,y),(x2-x1,y),(0,200,0),1)
    cv2.putText(c,str(y1+y),(4,y+22),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,255,0),2)
cv2.imencode(".png",cv2.resize(c,None,fx=sc,fy=sc,interpolation=cv2.INTER_CUBIC))[1].tofile(os.path.join(D,sys.argv[7]))
print("ok")
