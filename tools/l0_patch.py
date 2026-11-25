# -*- coding: utf-8 -*-
# 裁候选建筑patch供目检：编号 (名, x0,y0,x1,y1)
import cv2, numpy as np, os
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
l0=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","ladder","zoom_L0.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
g=l0[80:630,155:1060]
cands={
 "TH?":(415,260,495,340),
 "Eagle?":(555,125,635,205),
 "AD?":(185,120,245,180),
 "GoldStor?":(80,50,150,120),
 "Wiz?":(160,60,225,125),
}
row=[]
for name,(x0,y0,x1,y1) in cands.items():
    p=g[y0:y1,x0:x1]
    p=cv2.resize(p,None,fx=3,fy=3,interpolation=cv2.INTER_CUBIC)
    cv2.putText(p,name,(5,25),cv2.FONT_HERSHEY_SIMPLEX,0.8,(0,0,255),2)
    row.append(p)
h=max(p.shape[0] for p in row); row=[cv2.copyMakeBorder(p,0,h-p.shape[0],0,0,cv2.BORDER_CONSTANT) for p in row]
cv2.imencode(".png",np.hstack(row))[1].tofile(os.path.join(ROOT,"out","overlay","l0_patches.png"))
print("ok")
