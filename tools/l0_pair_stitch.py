# -*- coding: utf-8 -*-
# A/B 按链实测 dy=-418 放置；灰度相位缝；ORB复核重叠带；输出拼图
import os, cv2, numpy as np
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
A=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","l0_A.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
B=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","l0_B.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
dy=-418.0
H,W=A.shape[:2]
yB=int(round(-dy))
canvas=np.zeros((H+yB,W,3),np.uint8)
canvas[:H]=A
canvas[yB:yB+H]=B
# 重叠带相位相关（灰度）
ov=min(H,yB+H)-yB
gA=cv2.cvtColor(A,cv2.COLOR_BGR2GRAY).astype(np.float64)
gB=cv2.cvtColor(B,cv2.COLOR_BGR2GRAY).astype(np.float64)
bandA=gA[H-ov:,:]; bandB=gB[:ov,:]
win=cv2.createHanningWindow((W,ov),cv2.CV_64F)
(dx,ddy),resp=cv2.phaseCorrelate(bandA,bandB,win)
print(f"phase缝 dx={dx:.2f} dy={ddy:.2f} resp={resp:.3f} overlap={ov}px={ov/24:.1f}格")
# ORB 复核重叠带
det=cv2.ORB_create(1500)
ka,da=det.detectAndCompute(bandA.astype(np.uint8),None)
kb,db=det.detectAndCompute(bandB.astype(np.uint8),None)
bf=cv2.BFMatcher(cv2.NORM_HAMMING)
good=[m for m,n in bf.knnMatch(da,db,k=2) if m.distance<0.75*n.distance]
pa=np.float32([ka[m.queryIdx].pt for m in good]); pb=np.float32([kb[m.trainIdx].pt for m in good])
d=pb-pa; mx,my=np.median(d,axis=0)
inl=np.linalg.norm(d-[mx,my],axis=1)<12
print(f"ORB重叠带 inl={inl.sum()}/{len(good)} shift=({mx:.1f},{my:.1f})")
cv2.imencode(".png",canvas)[1].tofile(os.path.join(ROOT,"out","overlay","v6_L0_pair_stitched.png"))
print("canvas",canvas.shape,"总高",canvas.shape[0],"px =",round(canvas.shape[0]/24,1),"格")
