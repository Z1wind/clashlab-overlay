# -*- coding: utf-8 -*-
# 纯离线：ORB 试配 s1_full(原生全帧) 与 canvas 顶部带，判断是否同源可映射
import cv2, numpy as np, os
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
cv=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","v6_l0_three_shot_base.png"),dtype=np.uint8),0)
sf=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","l0three","s1_full.png"),dtype=np.uint8),0)
print("canvas",cv.shape,"s1",sf.shape)
orb=cv2.ORB_create(400)
for name,im in [("canvas_top",cv[:520,:]),("s1",sf)]:
    kp,des=orb.detectAndCompute(im,None)
    print(name,"kp",len(kp))
kc,dc=orb.detectAndCompute(cv[:520,:],None)
ks,ds=orb.detectAndCompute(sf,None)
bf=cv2.BFMatcher(cv2.NORM_HAMMING,crossCheck=False)
m=bf.knnMatch(dc,ds,k=2)
good=[a for a,b in m if a.distance<0.75*b.distance]
print("good matches",len(good))
