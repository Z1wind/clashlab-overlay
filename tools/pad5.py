# -*- coding: utf-8 -*-
# m5 金仓(3x3)：金(高饱和黄)+灰石板 联合掩膜，ROI内最大连通，外接框
import cv2, numpy as np, os
D=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\ladder"
img=cv2.imdecode(np.fromfile(os.path.join(D,"m5.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
hsv=cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
H,S,V=cv2.split(hsv)
# 金黄: H15-35 S>80 V>120 ; 灰石板: 低饱和 S<50, V60-200
gold=((H>=12)&(H<=38)&(S>70)&(V>120)).astype(np.uint8)
grey=((S<55)&(V>55)&(V<205)).astype(np.uint8)
m=((gold|grey)*255).astype(np.uint8)
roi=np.zeros_like(m); roi[270:610,300:600]=m[270:610,300:600]
roi=cv2.morphologyEx(roi,cv2.MORPH_OPEN,np.ones((5,5),np.uint8))
roi=cv2.morphologyEx(roi,cv2.MORPH_CLOSE,np.ones((21,21),np.uint8))
n,lab,stats,_=cv2.connectedComponentsWithStats(roi)
vis=img.copy()
best=None
for i in range(1,n):
    x,y,w,h,a=stats[i]
    if a>2000:
        print(f"comp x={x} y={y} W={w} H={h} area={a} W/3={w/3:.1f}")
        cv2.rectangle(vis,(x,y),(x+w,y+h),(0,0,255),2)
        if best is None or a>stats[best,4]: best=i
cv2.imencode(".png",vis)[1].tofile(os.path.join(D,"gs5_bbox.png"))
