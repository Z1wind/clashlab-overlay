# -*- coding: utf-8 -*-
# 纯离线：单点8x紧裁，6px刻度
import cv2, numpy as np, os, sys
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
im=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","v6_l0_three_shot_base.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
H,W=im.shape[:2]
BOXES=[
 ("goldNE",528,190,52),
 ("goldSW",210,592,52),
 ("goldSE",650,628,52),
 ("goldS",405,738,52),
 ("wizSE",660,660,52),
]
OUT=os.path.join(ROOT,"out","overlay","l0three","foot")
os.makedirs(OUT,exist_ok=True)
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
    cv2.imencode(".png",big)[1].tofile(os.path.join(OUT,nm+".png"))
print("done")
