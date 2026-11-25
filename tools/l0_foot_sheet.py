# -*- coding: utf-8 -*-
# 纯离线：5个候选底面紧裁8x合成sheet，6px细刻度，供读角
import cv2, numpy as np, os
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
im=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","v6_l0_three_shot_base.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
H,W=im.shape[:2]
# name,cx,cy,half
BOXES=[
 ("wiz_se",660,660,55),
 ("gold_ne",540,200,55),
 ("gold_sw",210,590,55),
 ("gold_se",648,628,55),
 ("gold_s",402,740,55),
]
tiles=[]
for nm,cx,cy,hh in BOXES:
    x0,y0=max(0,cx-hh),max(0,cy-hh); x1,y1=min(W,cx+hh),min(H,cy+hh)
    crop=im[y0:y1,x0:x1]
    z=8
    big=cv2.resize(crop,None,fx=z,fy=z,interpolation=cv2.INTER_CUBIC)
    bh,bw=big.shape[:2]
    for gx in range(x0//6*6,x1,6):
        u=(gx-x0)*z; cv2.line(big,(u,0),(u,bh),(0,0,255),1)
        if gx%24==0: cv2.putText(big,str(gx),(u+1,10),cv2.FONT_HERSHEY_SIMPLEX,0.3,(0,0,255),1)
    for gy in range(y0//6*6,y1,6):
        v=(gy-y0)*z; cv2.line(big,(0,v),(bw,v),(0,0,255),1)
        if gy%24==0: cv2.putText(big,str(gy),(1,v+9),cv2.FONT_HERSHEY_SIMPLEX,0.3,(0,0,255),1)
    cv2.putText(big,nm,(5,bh-8),cv2.FONT_HERSHEY_SIMPLEX,0.6,(0,255,0),2)
    tiles.append(big)
cols=2
rows=3
cw=max(t.shape[1] for t in tiles); ch=max(t.shape[0] for t in tiles)
sheet=np.full((rows*ch,cols*cw,3),30,np.uint8)
for k,t in enumerate(tiles):
    r,c=divmod(k,cols)
    sheet[r*ch:r*ch+t.shape[0],c*cw:c*cw+t.shape[1]]=t
cv2.imencode(".png",sheet)[1].tofile(os.path.join(ROOT,"out","overlay","l0three","footprint_sheet.png"))
print("done",sheet.shape)
