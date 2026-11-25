# -*- coding: utf-8 -*-
import cv2, numpy as np, os, sys
D=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\ladder"
img=cv2.imdecode(np.fromfile(os.path.join(D,"m2.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
x1,y1,x2,y2,scale=int(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4]),int(sys.argv[5]),float(sys.argv[6])
c=img[y1:y2,x1:x2].copy()
for x in range(0,x2-x1,10):
    cv2.line(c,(x,0),(x,y2-y1),(0,180,0),1);cv2.putText(c,str(x1+x),(x+1,9),cv2.FONT_HERSHEY_SIMPLEX,0.3,(0,255,0),1)
for y in range(0,y2-y1,10):
    cv2.line(c,(0,y),(x2-x1,y),(0,180,0),1);cv2.putText(c,str(y1+y),(2,y+9),cv2.FONT_HERSHEY_SIMPLEX,0.3,(0,255,0),1)
cv2.imencode(".png",cv2.resize(c,None,fx=scale,fy=scale,interpolation=cv2.INTER_CUBIC))[1].tofile(os.path.join(D,sys.argv[1]))
print("ok")
