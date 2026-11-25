# -*- coding: utf-8 -*-
# 纯离线：6x 候选建筑裁片，12px细刻度，v2晶格淡绿叠加(仅读中心用)
import cv2, numpy as np, os
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
im=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","v6_l0_three_shot_base.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
H,W=im.shape[:2]
O=np.array([473.2,796.6]); a=np.array([11.787,20.906]); b=np.array([-20.337,12.744])
# name,cx,cy,half
BOXES=[
 ("m_gne",540,185,75),
 ("m_gsw",200,585,75),
 ("m_gse",575,640,75),
 ("m_gs",400,745,75),
 ("m_ctower",415,455,90),
 ("m_thmain",560,500,90),
 ("m_wiz_se",655,690,70),
 ("m_airdef",555,480,80),
]
OUT=os.path.join(ROOT,"out","overlay","l0three","meas6")
os.makedirs(OUT,exist_ok=True)
for name,cx,cy,hh in BOXES:
    x0,y0=max(0,cx-hh),max(0,cy-hh); x1,y1=min(W,cx+hh),min(H,cy+hh)
    crop=im[y0:y1,x0:x1].copy()
    z=6
    big=cv2.resize(crop,None,fx=z,fy=z,interpolation=cv2.INTER_CUBIC)
    bh,bw=big.shape[:2]
    for gx in range(x0//12*12,x1,12):
        u=(gx-x0)*z; cv2.line(big,(u,0),(u,bh),(0,0,255),1)
        if gx%24==0: cv2.putText(big,str(gx),(u+2,11),cv2.FONT_HERSHEY_SIMPLEX,0.32,(0,0,255),1)
    for gy in range(y0//12*12,y1,12):
        v=(gy-y0)*z; cv2.line(big,(0,v),(bw,v),(0,0,255),1)
        if gy%24==0: cv2.putText(big,str(gy),(2,v+9),cv2.FONT_HERSHEY_SIMPLEX,0.32,(0,0,255),1)
    cv2.imencode(".png",big)[1].tofile(os.path.join(OUT,name+".png"))
print("done")
