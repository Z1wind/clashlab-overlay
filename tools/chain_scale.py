# -*- coding: utf-8 -*-
# 相邻帧 ORB 链：仿射缩放比 s_k，累积相对L0缩放；tile_px = 24.0 / cum_scale
import cv2, numpy as np, os, glob, sys
D=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\ladder"
files=sorted(glob.glob(os.path.join(D,"zoom_L*.png")), key=lambda p:int(p.split("L")[-1].split(".")[0]))
orb=cv2.ORB_create(800)
prev=cv2.imdecode(np.fromfile(files[0],dtype=np.uint8),cv2.IMREAD_GRAYSCALE)
kp0,des0=orb.detectAndCompute(prev,None)
cum=1.0
print("L0 tile_px=24.0 (全村44格实测基准) cum_scale=1.000")
for f in files[1:]:
    img=cv2.imdecode(np.fromfile(f,dtype=np.uint8),cv2.IMREAD_GRAYSCALE)
    kp,des=orb.detectAndCompute(img,None)
    bf=cv2.BFMatcher(cv2.NORM_HAMMING,crossCheck=False)
    knn=bf.knnMatch(des0,des,k=2)
    good=[m for m,n in knn if m.distance<0.75*n.distance]
    s=None
    if len(good)>=8:
        p0=np.float32([kp0[m.queryIdx].pt for m in good])
        p1=np.float32([kp[m.trainIdx].pt for m in good])
        M,inlier=cv2.estimateAffinePartial2D(p0,p1,method=cv2.RANSAC,ransacReprojThreshold=3)
        if M is not None:
            s=float(np.sqrt(M[0,0]**2+M[0,1]**2))
    if s: cum*=s
    name=os.path.basename(f)
    tp=24.0/cum
    print(f"{name}: matches={len(good)} s={s if s else float('nan'):.3f} cum={cum:.3f} tile_px={tp:.2f}")
    kp0,des0=kp,des
