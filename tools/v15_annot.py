# -*- coding: utf-8 -*-
# v15_annot.py — 对指定帧画10px坐标网格裁块，人工量底面。新文件。
import os, cv2, numpy as np, sys
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
EN = os.path.join(ROOT, "out", "overlay", "enemy")
src = sys.argv[1] if len(sys.argv)>1 else "zoom1.png"
outpref = sys.argv[2] if len(sys.argv)>2 else "z"
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
annot((470,140,730,430),f"{outpref}_th.png",10,2.6)
annot((150,70,390,280),f"{outpref}_goldNW.png",10,3.0)
annot((820,80,1060,290),f"{outpref}_goldNE.png",10,3.0)
annot((150,480,390,690),f"{outpref}_goldSW.png",10,3.0)
print("ok")
