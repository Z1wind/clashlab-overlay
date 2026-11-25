# -*- coding: utf-8 -*-
# HoughLinesP 在mask3_c轮廓上找边界段，按角度聚类，输出各段
import cv2, numpy as np, os, json
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
im=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","v6_l0_two_shot_base.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
m=cv2.inRange(hsv,np.array([30,40,180]),np.array([90,150,255]))
m[hsv[:,:,0]>95]=0
m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((25,25),np.uint8))
cnts,_=cv2.findContours(m,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
cnt=max(cnts,key=cv2.contourArea)
edge=np.zeros(m.shape,np.uint8); cv2.drawContours(edge,[cnt],-1,255,2)
lines=cv2.HoughLinesP(edge,1,np.pi/1800,threshold=40,minLineLength=60,maxLineGap=20)
segs=[]
dbg=im.copy()
if lines is not None:
    for l in lines.reshape(-1,4):
        x1,y1,x2,y2=l
        dx,dy=x2-x1,y2-y1
        ang=np.degrees(np.arctan2(dy,dx))
        length=np.hypot(dx,dy)
        segs.append((int(x1),int(y1),int(x2),int(y2),round(ang,1),round(length,1)))
    segs.sort(key=lambda s:-s[5])
    for s in segs[:25]:
        print(s)
        cv2.line(dbg,(s[0],s[1]),(s[2],s[3]),(0,255,0),1)
cv2.imencode(".png",dbg)[1].tofile(os.path.join(ROOT,"out","overlay","l0new","hough.png"))
