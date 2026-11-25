# -*- coding: utf-8 -*-
# 裁 m2 金仓/墙段，20px网格，存 ladder
import cv2, numpy as np, os, sys
D=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\ladder"
src=sys.argv[1] if len(sys.argv)>1 else "m2.png"
img=cv2.imdecode(np.fromfile(os.path.join(D,src),dtype=np.uint8),cv2.IMREAD_COLOR)
def crop(name,x1,y1,x2,y2,scale=1.8):
    c=img[y1:y2,x1:x2].copy()
    for x in range(0,x2-x1,20):
        cv2.line(c,(x,0),(x,y2-y1),(0,180,0),1);cv2.putText(c,str(x1+x),(x+1,10),cv2.FONT_HERSHEY_SIMPLEX,0.35,(0,255,0),1)
    for y in range(0,y2-y1,20):
        cv2.line(c,(0,y),(x2-x1,y),(0,180,0),1);cv2.putText(c,str(y1+y),(2,y+10),cv2.FONT_HERSHEY_SIMPLEX,0.35,(0,255,0),1)
    cv2.imencode(".png",cv2.resize(c,None,fx=scale,fy=scale,interpolation=cv2.INTER_CUBIC))[1].tofile(os.path.join(D,name))
crop("gs_pad.png",280,280,620,610)
crop("wall_run.png",520,380,1010,640)
print("ok")
