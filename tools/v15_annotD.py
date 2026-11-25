# -*- coding: utf-8 -*-
# v15_annotD.py — 默认档候选建筑裁块标注。新文件。
import os, cv2, numpy as np, sys
R = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\_recon"
src = sys.argv[1]; pref = sys.argv[2]
im = cv2.imdecode(np.fromfile(os.path.join(R,src),dtype=np.uint8),cv2.IMREAD_COLOR)
def annot(box,name,step=10,scale=2.8):
    x1,y1,x2,y2=box
    c=im[y1:y2,x1:x2].copy()
    for x in range(0,c.shape[1],step):
        cv2.line(c,(x,0),(x,c.shape[0]),(0,255,255),1)
        cv2.putText(c,str(x1+x),(x+1,11),cv2.FONT_HERSHEY_SIMPLEX,0.3,(0,255,255),1)
    for y in range(0,c.shape[0],step):
        cv2.line(c,(0,y),(c.shape[1],y),(0,255,255),1)
        cv2.putText(c,str(y1+y),(1,y+9),cv2.FONT_HERSHEY_SIMPLEX,0.3,(0,255,255),1)
    c=cv2.resize(c,None,fx=scale,fy=scale,interpolation=cv2.INTER_NEAREST)
    cv2.imencode(".png",c)[1].tofile(os.path.join(R,name))
# TH 4x4 中心
annot((560,280,730,430),f"{pref}_th.png",10,2.6)
# 西翼候选
annot((180,300,360,430),f"{pref}_w1.png",10,2.8)
# 东翼候选
annot((900,300,1080,430),f"{pref}_e1.png",10,2.8)
# 北翼
annot((400,150,560,280),f"{pref}_n1.png",10,2.8)
# 南翼
annot((560,460,740,600),f"{pref}_s1.png",10,2.8)
print("ok")
