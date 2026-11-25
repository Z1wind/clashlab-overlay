# -*- coding: utf-8 -*-
# m2 金仓石板底座：低饱和灰(非金非绿)掩膜，ROI内最大连通，外框
import cv2, numpy as np, os
D=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\ladder"
img=cv2.imdecode(np.fromfile(os.path.join(D,"m2.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
b,g,r=cv2.split(img.astype(int))
mx=np.maximum(np.maximum(b,g),r); mn=np.minimum(np.minimum(b,g),r)
sat=mx-mn
# 灰石板: 低饱和, 明度 70-190, 非绿
grey=((sat<45)&(mx>60)&(mx<200)).astype(np.uint8)*255
roi=np.zeros_like(grey); roi[440:600,310:590]=grey[440:600,310:590]
roi=cv2.morphologyEx(roi,cv2.MORPH_CLOSE,np.ones((9,9),np.uint8))
n,lab,stats,_=cv2.connectedComponentsWithStats(roi)
vis=img.copy()
for i in range(1,n):
    x,y,w,h,a=stats[i]
    if a>1500:
        print(f"灰组件 x={x} y={y} W={w} H={h} area={a} W/3={w/3:.1f}")
        cv2.rectangle(vis,(x,y),(x+w,y+h),(0,0,255),2)
cv2.imencode(".png",vis)[1].tofile(os.path.join(D,"gs_grey.png"))
