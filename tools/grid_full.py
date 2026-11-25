# -*- coding: utf-8 -*-
import cv2, numpy as np, os, sys
D=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\ladder"
img=cv2.imdecode(np.fromfile(os.path.join(D,sys.argv[1]),dtype=np.uint8),cv2.IMREAD_COLOR)
c=img.copy()
for x in range(0,1280,40):
    cv2.line(c,(x,0),(x,720),(0,180,0),1);cv2.putText(c,str(x),(x+2,15),cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,255,0),1)
for y in range(0,720,40):
    cv2.line(c,(0,y),(1280,y),(0,180,0),1);cv2.putText(c,str(y),(2,y+12),cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,255,0),1)
cv2.imencode(".png",c)[1].tofile(os.path.join(D,sys.argv[2]))
print("ok")
