# -*- coding: utf-8 -*-
# dup_check.py — 拼接图全局自相似：滑窗 ORB/NCC 找重复内容区域
import cv2, numpy as np, os, sys
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p=os.path.join(ROOT,"out","overlay","v6_stitched_base.png")
im=cv2.imdecode(np.fromfile(p,dtype=np.uint8),cv2.IMREAD_COLOR)
g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
H,W=g.shape
print("canvas",W,H)
# 分块网格 220x220，步长110，块间 ORB 匹配计数
orb=cv2.ORB_create(500)
step=110; bs=220
cells=[]
for y in range(0,H-bs,step):
    for x in range(0,W-bs,step):
        c=g[y:y+bs,x:x+bs]
        kp,des=orb.detectAndCompute(c,None)
        cells.append((x,y,kp,des))
bf=cv2.BFMatcher(cv2.NORM_HAMMING)
hits=[]
for i in range(len(cells)):
    xi,yi,ki,di=cells[i]
    if di is None: continue
    for j in range(i+1,len(cells)):
        xj,yj,kj,dj=cells[j]
        if dj is None: continue
        m=bf.knnMatch(di,dj,k=2)
        good=[a for a,b in m if a.distance<0.75*b.distance]
        if len(good)>=15:
            # 中位位移
            pa=np.float32([ki[a.queryIdx].pt for a in good])
            pb=np.float32([kj[a.trainIdx].pt for a in good])
            d=pb-pa; mx,my=np.median(d,axis=0)
            shift=np.hypot(mx,my)
            hits.append((xi,yi,xj,yj,len(good),round(mx,0),round(my,0),round(shift,0)))
for h in sorted(hits,key=lambda r:-r[4])[:25]:
    print(f"A({h[0]},{h[1]}) B({h[2]},{h[3]}) matches={h[4]} shift=({h[5]},{h[6]}) |d|={h[7]}")
