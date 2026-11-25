# -*- coding: utf-8 -*-
# L1 链上 acc 放置；相邻对 ORB 残差；输出 v6_L1_6blocks.png
import json, os, cv2, numpy as np
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT=os.path.join(ROOT,"out","overlay","blocks_L1")
log=json.load(open(os.path.join(OUT,"l1_log.json"),encoding="utf-8"))
det=cv2.ORB_create(1500)
items=[]
for t in log:
    im=cv2.imdecode(np.fromfile(os.path.join(OUT,t["file"]),dtype=np.uint8),cv2.IMREAD_COLOR)
    acc=t.get("acc",[0,0])
    items.append((t["file"],im,acc[0],acc[1]))
minx=min(i[2] for i in items); miny=min(i[3] for i in items)
H,W=items[0][1].shape[:2]
maxx=int(np.ceil(max(i[2]-minx+W for i in items)))
maxy=int(np.ceil(max(i[3]-miny+H for i in items)))
canvas=np.zeros((maxy,maxx,3),np.uint8)
for f,im,x,y in items:
    canvas[int(round(y-miny)):int(round(y-miny))+H,int(round(x-minx)):int(round(x-minx))+W]=im
# 相邻链 ORB 残差
def orb(a,b):
    ka,da=det.detectAndCompute(cv2.cvtColor(a,cv2.COLOR_BGR2GRAY),None)
    kb,db=det.detectAndCompute(cv2.cvtColor(b,cv2.COLOR_BGR2GRAY),None)
    bf=cv2.BFMatcher(cv2.NORM_HAMMING)
    good=[m for m,n in bf.knnMatch(da,db,k=2) if m.distance<0.75*n.distance]
    if len(good)<10: return None,0
    pa=np.float32([ka[m.queryIdx].pt for m in good]); pb=np.float32([kb[m.trainIdx].pt for m in good])
    d=pb-pa; mx,my=np.median(d,axis=0)
    inl=np.linalg.norm(d-[mx,my],axis=1)<12
    return (float(mx),float(my)),int(inl.sum())
worst=0
for k in range(1,len(items)):
    s,n=orb(items[k-1][1],items[k][1])
    ex=items[k][2]-items[k-1][2]; ey=items[k][3]-items[k-1][3]
    if s:
        r=float(np.hypot(s[0]-ex,s[1]-ey)); worst=max(worst,r)
        print(f"{items[k-1][0]}->{items[k][0]} exp=({ex:.0f},{ey:.0f}) meas=({s[0]:.0f},{s[1]:.0f}) resid={r:.1f} n={n}")
    else:
        print(items[k-1][0],"->",items[k][0],"NO MATCH n=",n)
cv2.imencode(".png",canvas)[1].tofile(os.path.join(ROOT,"out","overlay","v6_L1_6blocks.png"))
print("worst=",round(worst,1),"canvas",canvas.shape)
