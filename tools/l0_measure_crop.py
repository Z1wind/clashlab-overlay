# -*- coding: utf-8 -*-
# 纯离线：围绕候选建筑出4x放大裁片，带12px细坐标刻度(画布坐标标注)，供人工读角点
import cv2, numpy as np, os, sys
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
im=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","v6_l0_three_shot_base.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
H,W=im.shape[:2]
# (name, cx, cy, half=90)
BOXES=[
 ("g_nw",240,285,95),
 ("g_ne",505,150,95),
 ("g_sw1",185,565,95),
 ("g_se",610,605,95),
 ("g_s",400,720,95),
 ("th_main",600,490,110),
 ("c_tower",415,455,100),
]
OUT=os.path.join(ROOT,"out","overlay","l0three","meas")
os.makedirs(OUT,exist_ok=True)
for name,cx,cy,hh in BOXES:
    x0,y0=max(0,cx-hh),max(0,cy-hh)
    x1,y1=min(W,cx+hh),min(H,cy+hh)
    crop=im[y0:y1,x0:x1]
    z=4
    big=cv2.resize(crop,None,fx=z,fy=z,interpolation=cv2.INTER_CUBIC)
    bh,bw=big.shape[:2]
    # 刻度：每12px(原图)一条
    for gx in range(x0//12*12,x1,12):
        u=(gx-x0)*z
        cv2.line(big,(u,0),(u,bh),(0,0,255),1)
        if gx%24==0: cv2.putText(big,str(gx),(u+2,12),cv2.FONT_HERSHEY_SIMPLEX,0.35,(0,0,255),1)
    for gy in range(y0//12*12,y1,12):
        v=(gy-y0)*z
        cv2.line(big,(0,v),(bw,v),(0,0,255),1)
        if gy%24==0: cv2.putText(big,str(gy),(2,v+10),cv2.FONT_HERSHEY_SIMPLEX,0.35,(0,0,255),1)
    cv2.imencode(".png",big)[1].tofile(os.path.join(OUT,name+".png"))
    print(name,x0,y0,x1,y1)
print("done")
