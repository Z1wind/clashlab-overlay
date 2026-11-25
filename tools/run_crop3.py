# -*- coding: utf-8 -*-
# L3 底部长墙 + L1 中部，20px网格
import cv2, numpy as np, os
D=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\ladder"
def crop(src,name,x1,y1,x2,y2,scale=1.5):
    img=cv2.imdecode(np.fromfile(os.path.join(D,src),dtype=np.uint8),cv2.IMREAD_COLOR)
    c=img[y1:y2,x1:x2].copy()
    for x in range(0,x2-x1,20):
        cv2.line(c,(x,0),(x,y2-y1),(0,180,0),1); cv2.putText(c,str(x1+x),(x+1,12),cv2.FONT_HERSHEY_SIMPLEX,0.35,(0,255,0),1)
    for y in range(0,y2-y1,20):
        cv2.line(c,(0,y),(x2-x1,y),(0,180,0),1); cv2.putText(c,str(y1+y),(2,y+12),cv2.FONT_HERSHEY_SIMPLEX,0.35,(0,255,0),1)
    cv2.imencode(".png",cv2.resize(c,None,fx=scale,fy=scale,interpolation=cv2.INTER_CUBIC))[1].tofile(os.path.join(D,name))
crop("zoom_L3.png","run_L3_bottom.png",150,380,760,680)
crop("zoom_L1.png","run_L1_mid.png",100,80,1180,620,1.0)
print("ok")
