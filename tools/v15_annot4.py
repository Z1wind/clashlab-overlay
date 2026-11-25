# -*- coding: utf-8 -*-
import os, cv2, numpy as np, sys
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
EN = os.path.join(ROOT, "out", "overlay", "enemy")
src=sys.argv[1]; pref=sys.argv[2]
im = cv2.imdecode(np.fromfile(os.path.join(EN,src),dtype=np.uint8),cv2.IMREAD_COLOR)
def annot(box,name,step=10,scale=3.0):
    x1,y1,x2,y2=box
    c=im[y1:y2,x1:x2].copy()
    for x in range(0,c.shape[1],step):
        cv2.line(c,(x,0),(x,c.shape[0]),(0,255,255),1)
        cv2.putText(c,str(x1+x),(x+1,11),cv2.FONT_HERSHEY_SIMPLEX,0.3,(0,255,255),1)
    for y in range(0,c.shape[0],step):
        cv2.line(c,(0,y),(c.shape[1],y),(0,255,255),1)
        cv2.putText(c,str(y1+y),(1,y+9),cv2.FONT_HERSHEY_SIMPLEX,0.3,(0,255,255),1)
    c=cv2.resize(c,None,fx=scale,fy=scale,interpolation=cv2.INTER_NEAREST)
    cv2.imencode(".png",c)[1].tofile(os.path.join(EN,name))
annot((850,230,1030,410),f"{pref}_drumR.png",10,3.2)
annot((150,280,340,450),f"{pref}_cannonL.png",10,3.2)
annot((560,30,780,260),f"{pref}_th.png",10,3.2)
print("ok")
