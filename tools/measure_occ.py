# -*- coding: utf-8 -*-
# measure_occ.py — Step1: 15块可见画布上的实占外接格数；L0 帧上量平台菱形与建筑外接
import json, os, cv2, numpy as np
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BLK=os.path.join(ROOT,"out","overlay","blocks3")
log=json.load(open(os.path.join(BLK,"collect_log.json"),encoding="utf-8"))

# --- (a) 仅用 log[0:15] 重建首轮15块画布（place.py 同逻辑）---
items=[]; cx=cy=0.0
for t in log["tiles"][:15]:
    im=cv2.imdecode(np.fromfile(os.path.join(BLK,t["file"]),dtype=np.uint8),cv2.IMREAD_COLOR)
    im=im[:,:905]
    cx+=t["dx"]; cy+=t["dy"]
    items.append((im,cx,cy))
minx=min(i[1] for i in items); miny=min(i[2] for i in items)
H,W=items[0][0].shape[:2]
maxx=int(np.ceil(max(i[1]-minx+W for i in items))); maxy=int(np.ceil(max(i[2]-miny+H for i in items)))
canvas=np.zeros((maxy,maxx,3),np.uint8)
for im,x,y in items:
    canvas[int(round(y-miny)):int(round(y-miny))+H,int(round(x-minx)):int(round(x-minx))+W]=im
cv2.imencode(".png",canvas)[1].tofile(os.path.join(ROOT,"out","overlay","v6_15block_canvas.png"))
mask=np.any(canvas>8,axis=2)
ys,xs=np.where(mask)
x0,x1,y0,y1=xs.min(),xs.max(),ys.min(),ys.max()
print(f"[15块画布] 画布 {W and maxx}x{maxy} 非空bbox x{x0}-{x1} y{y0}-{y1} = {x1-x0+1}x{y1-y0+1}px")
print(f"  /80px每格 -> 可见实占约 {round((x1-x0+1)/80,1)} x {round((y1-y0+1)/80,1)} 格（仅首轮覆盖带，非全阵）")

# --- (b) L0 帧：裁游戏区，量平台菱形边界与建筑外接（24px/格）---
l0=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","ladder","zoom_L0.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
print("L0 frame",l0.shape)
# UI 裁口：顶资源条、左名牌/按钮列、底任务栏、右导轨
g=l0[80:630,155:1060]
gray=cv2.cvtColor(g,cv2.COLOR_BGR2GRAY)
# 平台草地：绿 HSV
hsv=cv2.cvtColor(g,cv2.COLOR_BGR2HSV)
green=cv2.inRange(hsv,np.array([35,40,40]),np.array([90,255,255]))
# 形态学闭运算填建筑洞
k=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(31,31))
gm=cv2.morphologyEx(green,cv2.MORPH_CLOSE,k)
gm=cv2.morphologyEx(gm,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(15,15)))
n,lab,stats,_=cv2.connectedComponentsWithStats(gm)
big=max(range(1,n),key=lambda i:stats[i,cv2.CC_STAT_AREA])
bx0,by0,bw,bh,ba=stats[big]
print(f"[L0 平台草地块] bbox x{bx0}-{bx0+bw} y{by0}-{by0+bh} {bw}x{bh}px area={ba}")
print(f"  /24px每格 -> 平台约 {round(bw/24,1)} x {round(bh/24,1)} 格（菱形外接矩形）")
# 建筑外接：非草地且非黑的彩色内容，在草地块内部
inside=(lab==big)
nongrass=((green<40)&inside)
ys2,xs2=np.where(nongrass)
if len(xs2):
    print(f"[L0 建筑实占] bbox {xs2.min()}-{xs2.max()} x {ys2.min()}-{ys2.max()} = {xs2.max()-xs2.min()+1}x{ys2.max()-ys2.min()+1}px -> {round((xs2.max()-xs2.min()+1)/24,1)} x {round((ys2.max()-ys2.min()+1)/24,1)} 格")
vis=g.copy(); cv2.rectangle(vis,(bx0,by0),(bx0+bw,by0+bh),(0,0,255),2)
cv2.imencode(".png",vis)[1].tofile(os.path.join(ROOT,"out","overlay","l0_platform_bbox.png"))
