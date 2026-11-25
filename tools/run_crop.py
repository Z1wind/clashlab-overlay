# -*- coding: utf-8 -*-
# L14 底部长墙段裁 + 20px网格，供数块
import cv2, numpy as np, os
D=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\ladder"
img=cv2.imdecode(np.fromfile(os.path.join(D,"zoom_L14.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
x1,y1,x2,y2=120,330,780,660
c=img[y1:y2,x1:x2].copy()
for x in range(0,x2-x1,20):
    cv2.line(c,(x,0),(x,y2-y1),(0,180,0),1)
    cv2.putText(c,str(x1+x),(x+1,12),cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,255,0),1)
for y in range(0,y2-y1,20):
    cv2.line(c,(0,y),(x2-x1,y),(0,180,0),1)
    cv2.putText(c,str(y1+y),(2,y+12),cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,255,0),1)
cv2.imencode(".png",cv2.resize(c,None,fx=1.5,fy=1.5,interpolation=cv2.INTER_CUBIC))[1].tofile(os.path.join(D,"run_L14_grid.png"))
print("ok")
