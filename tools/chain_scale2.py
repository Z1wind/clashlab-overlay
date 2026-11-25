# -*- coding: utf-8 -*-
# 相邻帧 homography 缩放链（H 分解 s=sqrt(H00^2+H10^2)），L0=24px基准
import cv2, numpy as np, os, glob
D=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\ladder"
files=sorted(glob.glob(os.path.join(D,"zoom_L*.png")), key=lambda p:int(p.split("L")[-1].split(".")[0]))
orb=cv2.ORB_create(800)
prev=cv2.imdecode(np.fromfile(files[0],dtype=np.uint8),cv2.IMREAD_GRAYSCALE)
kp0,des0=orb.detectAndCompute(prev,None)
cum=1.0
print("L0 tile_px=24.00 cum=1.000")
for f in files[1:]:
    img=cv2.imdecode(np.fromfile(f,dtype=np.uint8),cv2.IMREAD_GRAYSCALE)
    kp,des=orb.detectAndCompute(img,None)
    bf=cv2.BFMatcher(cv2.NORM_HAMMING)
    knn=bf.knnMatch(des0,des,k=2)
    good=[m for m,n in knn if m.distance<0.75*n.distance]
    s=None
    if len(good)>=10:
        p0=np.float32([kp0[m.queryIdx].pt for m in good])
        p1=np.float32([kp[m.trainIdx].pt for m in good])
        H,_=cv2.findHomography(p0,p1,cv2.RANSAC,4)
        if H is not None:
            s=float(np.sqrt(H[0,0]**2+H[0,1]**2))
    if s and np.isfinite(s): cum*=s
    print(f"{os.path.basename(f)}: n={len(good)} s={s if s else float('nan'):.3f} cum={cum:.3f} tile_px={24/cum:.2f}")
    kp0,des0=kp,des
