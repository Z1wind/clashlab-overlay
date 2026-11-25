# -*- coding: utf-8 -*-
# v15_annotM.py — 最大档候选建筑裁块标注（5px 网格）。新文件。
import os, cv2, numpy as np, sys
R = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\_recon"
src = sys.argv[1]; pref = sys.argv[2]
im = cv2.imdecode(np.fromfile(os.path.join(R,src),dtype=np.uint8),cv2.IMREAD_COLOR)
def annot(box,name,step=5,scale=3.0):
    x1,y1,x2,y2=box
    c=im[y1:y2,x1:x2].copy()
    for x in range(0,c.shape[1],step):
        cv2.line(c,(x,0),(x,c.shape[0]),(0,255,255),1)
        if step==5 or x%10==0:
            cv2.putText(c,str(x1+x),(x+1,11),cv2.FONT_HERSHEY_SIMPLEX,0.35,(0,255,255),1)
    for y in range(0,c.shape[0],step):
        cv2.line(c,(0,y),(c.shape[1],y),(0,255,255),1)
        if step==5 or y%10==0:
            cv2.putText(c,str(y1+y),(1,y+9),cv2.FONT_HERSHEY_SIMPLEX,0.35,(0,255,255),1)
    c=cv2.resize(c,None,fx=scale,fy=scale,interpolation=cv2.INTER_NEAREST)
    cv2.imencode(".png",c)[1].tofile(os.path.join(R,name))
annot((160,170,480,420),f"{pref}_spelltower.png")
annot((960,290,1180,460),f"{pref}_cannon.png")
annot((520,140,840,430),f"{pref}_clancastle.png")
print("ok")
