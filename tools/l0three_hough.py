# -*- coding: utf-8 -*-
import cv2, numpy as np, os
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
im=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","v6_l0_three_shot_base.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
m=cv2.inRange(hsv,np.array([30,40,180]),np.array([90,150,255]))
m[hsv[:,:,0]>95]=0
m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((25,25),np.uint8))
cnts,_=cv2.findContours(m,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
cnt=max(cnts,key=cv2.contourArea)
edge=np.zeros(m.shape,np.uint8); cv2.drawContours(edge,[cnt],-1,255,2)
lines=cv2.HoughLinesP(edge,1,np.pi/1800,threshold=40,minLineLength=80,maxLineGap=25)
segs=[]
for l in lines.reshape(-1,4):
    x1,y1,x2,y2=map(int,l); dx,dy=x2-x1,y2-y1
    if abs(dx)<5: continue
    ang=np.degrees(np.arctan2(dy,dx)); length=np.hypot(dx,dy)
    segs.append((x1,y1,x2,y2,round(ang,1),round(length,1)))
segs.sort(key=lambda s:-s[5])
for s in segs[:30]: print(s)
dbg=im.copy()
for s in segs[:30]: cv2.line(dbg,(s[0],s[1]),(s[2],s[3]),(0,255,0),1)
cv2.imencode(".png",dbg)[1].tofile(os.path.join(ROOT,"out","overlay","l0three","hough3.png"))
