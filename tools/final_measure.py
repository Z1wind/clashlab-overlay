# -*- coding: utf-8 -*-
# 最终量测：zoom_L0 参考帧上 建筑实占bbox(px→24px/格)；平台草坪连通域bbox
import cv2, numpy as np, os
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
l0=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","ladder","zoom_L0.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
g=l0[80:630,155:1060]
hsv=cv2.cvtColor(g,cv2.COLOR_BGR2HSV)
H,W=g.shape[:2]
# 森林暗绿 V<110 S>150；水面蓝；其余=草地/建筑/墙
forest=cv2.inRange(hsv,np.array([35,150,20]),np.array([80,255,115]))
water=cv2.inRange(hsv,np.array([90,40,120]),np.array([135,120,255]))
bg=((forest>0)|(water>0)).astype(np.uint8)*255
# 建筑/墙：高饱和非森林非水
build=((cv2.bitwise_not(bg))>0)
# 去掉纯草坪亮绿(低饱和?草坪S~180)：用边缘/颜色多样，直接取非背景连通域最大=平台
free=(bg==0).astype(np.uint8)*255
free=cv2.morphologyEx(free,cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(25,25)))
n,lab,stats,_=cv2.connectedComponentsWithStats(free)
big=max(range(1,n),key=lambda i:stats[i,cv2.CC_STAT_AREA])
bx,by,bw,bh,ba=stats[big]
print(f"平台连通域 bbox {bw}x{bh}px -> {bw/24:.1f}x{bh/24:.1f}格 area{ba}")
# 建筑实占：平台内、非草坪(草坪亮绿H30-45 S120-220 V120-220)
lawn=cv2.inRange(hsv,np.array([28,110,115]),np.array([46,225,228]))
inside=(lab==big)
nonlawn=((lawn<40)&inside)
ys,xs=np.where(nonlawn)
print(f"建筑实占 bbox {xs.max()-xs.min()+1}x{ys.max()-ys.min()+1}px @({xs.min()},{ys.min()}) -> {(xs.max()-xs.min()+1)/24:.1f}x{(ys.max()-ys.min()+1)/24:.1f}格")
vis=g.copy(); cv2.rectangle(vis,(bx,by),(bx+bw,by+bh),(0,0,255),2)
cv2.imencode(".png",vis)[1].tofile(os.path.join(ROOT,"out","overlay","final_bbox.png"))
