# -*- coding: utf-8 -*-
# L0 平台测量：草坪连通域 + 金墙轮廓；输出 bbox（24px/格）
import cv2, numpy as np, os
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
l0=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","ladder","zoom_L0.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
g=l0[80:630,155:1060]
hsv=cv2.cvtColor(g,cv2.COLOR_BGR2HSV)
lawn=cv2.inRange(hsv,np.array([25,120,120]),np.array([45,220,225]))
# 金/白外墙（浅米色）
wall=cv2.inRange(hsv,np.array([15,20,180]),np.array([45,90,255]))
# 森林暗绿排除后，取 lawn 最大内孔：先填森林
forest=cv2.inRange(hsv,np.array([40,200,30]),np.array([75,255,110]))
free=((lawn>0)|(wall>0))&(forest==0)
free=free.astype(np.uint8)*255
free=cv2.morphologyEx(free,cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(31,31)))
n,lab,stats,_=cv2.connectedComponentsWithStats(free)
order=sorted(range(1,n),key=lambda i:-stats[i,cv2.CC_STAT_AREA])[:5]
for i in order:
    print("comp",stats[i].tolist())
big=order[0]
bx,by,bw,bh,ba=stats[big]
print(f"平台 bbox {bw}x{bh}px -> {bw/24.0:.1f}x{bh/24.0:.1f}格 area{ba}")
inside=(lab==big)
nonlawn=((free<40)&inside)
ys,xs=np.where(nonlawn)
if len(xs):
    print(f"建筑实占 {xs.max()-xs.min()+1}x{ys.max()-ys.min()+1}px -> {(xs.max()-xs.min()+1)/24.0:.1f}x{(ys.max()-ys.min()+1)/24.0:.1f}格 @({xs.min()},{ys.min()})")
vis=g.copy(); cv2.rectangle(vis,(bx,by),(bx+bw,by+bh),(0,0,255),2)
cv2.imencode(".png",vis)[1].tofile(os.path.join(ROOT,"out","overlay","l0_plat.png"))
cv2.imencode(".png",free)[1].tofile(os.path.join(ROOT,"out","overlay","l0_mask.png"))
