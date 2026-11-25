# -*- coding: utf-8 -*-
# 正确版：当前帧 vs zoom_L0，参考图按s缩放后重算ORB，找最佳s；tile_px=24.0/s
import cv2, numpy as np, os
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
cur=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","l0new","l0_min.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
ref=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","ladder","zoom_L0.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
CROP=(155,80,1105,630)
cur=cur[CROP[1]:CROP[3],CROP[0]:CROP[2]]; ref=ref[CROP[1]:CROP[3],CROP[0]:CROP[2]]
orb=cv2.ORB_create(1500)
ka,da=orb.detectAndCompute(cv2.cvtColor(cur,cv2.COLOR_BGR2GRAY),None)
best=(-1,None,None)
h,w=ref.shape[:2]
for s in np.arange(1.00,1.16,0.01):
    rs=cv2.resize(ref,None,fx=s,fy=s,interpolation=cv2.INTER_CUBIC)
    rh,rw=rs.shape[:2]
    if rh<h or rw<w: continue
    y0=(rh-h)//2; x0=(rw-w)//2
    rsc=rs[y0:y0+h,x0:x0+w]
    kb,db=orb.detectAndCompute(cv2.cvtColor(rsc,cv2.COLOR_BGR2GRAY),None)
    bf=cv2.BFMatcher(cv2.NORM_HAMMING)
    good=[m for m,n in bf.knnMatch(da,db,k=2) if m.distance<0.75*n.distance]
    if len(good)<10: print(f"s={s:.2f} good={len(good)}"); continue
    pa=np.float32([ka[m.queryIdx].pt for m in good]); pb=np.float32([kb[m.trainIdx].pt for m in good])
    d=pb-pa; mx,my=np.median(d,axis=0)
    inl=np.linalg.norm(d-[mx,my],axis=1)<15
    n=int(inl.sum())
    print(f"s={s:.2f} inl={n} good={len(good)} shift=({mx:.0f},{my:.0f})")
    if n>best[0]: best=(n,s,(float(mx),float(my)))
print("BEST",best,"tile_px=",round(24.0/best[1],2))
