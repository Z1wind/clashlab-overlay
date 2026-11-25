# -*- coding: utf-8 -*-
import cv2, numpy as np, os, math
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
CANVAS = os.path.join(ROOT, "out", "overlay", "v6_l0_three_shot_base.png")
A = np.array([13.17, 23.36]); B = np.array([-20.06, 12.57])
ua = A/np.linalg.norm(A); ub = B/np.linalg.norm(B)
img = cv2.imdecode(np.fromfile(CANVAS, np.uint8), cv2.IMREAD_COLOR)
b, g, r = img[:,:,0], img[:,:,1], img[:,:,2]
mask = ((r>190)&(g>160)&(b<90)).astype(np.uint8)*255
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((2,2),np.uint8))
n,lab,stats,cent = cv2.connectedComponentsWithStats(mask)
pts=[]
for i in range(1,n):
    area=stats[i,cv2.CC_STAT_AREA]; x,y,w,h=stats[i,:4]
    if 25<=area<=160 and w<=26 and h<=26 and 330<cent[i][0]<730 and 280<cent[i][1]<580:
        pts.append(tuple(cent[i]))
P=np.array(pts)
print("pts:", [(round(x),round(y)) for x,y in pts])
for i in range(len(P)):
    for j in range(i+1,len(P)):
        d=P[j]-P[i]; dist=np.linalg.norm(d)
        if 16<dist<34:
            ta=abs(float(d@ua)); tb=abs(float(d@ub))
            ang=math.degrees(math.atan2(d[1],d[0]))
            print(f"({P[i][0]:.0f},{P[i][1]:.0f})->({P[j][0]:.0f},{P[j][1]:.0f}) dist={dist:.1f} ta={ta:.1f} tb={tb:.1f} ang={ang:.0f}")
