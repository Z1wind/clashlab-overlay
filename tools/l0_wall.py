# -*- coding: utf-8 -*-
# 金墙轮廓法：浅色外墙阈值 → 最大外轮廓 → bbox（平台菱形外接）
import cv2, numpy as np, os
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
l0=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","ladder","zoom_L0.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
g=l0[80:630,155:1060]
hsv=cv2.cvtColor(g,cv2.COLOR_BGR2HSV)
wall=cv2.inRange(hsv,np.array([12,15,170]),np.array([48,100,255]))
wall=cv2.morphologyEx(wall,cv2.MORPH_CLOSE,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(7,7)))
cnts,_=cv2.findContours(wall,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
cnts=sorted(cnts,key=cv2.contourArea,reverse=True)[:8]
vis=g.copy()
for i,c in enumerate(cnts):
    x,y,w,h=cv2.boundingRect(c); a=cv2.contourArea(c)
    print(f"contour{i} bbox{x},{y} {w}x{h} area{a:.0f} -> {w/24:.1f}x{h/24:.1f}格")
    cv2.rectangle(vis,(x,y),(x+w,y+h),(0,0,255),2); cv2.putText(vis,str(i),(x,y-5),1,1,(0,0,255),2)
cv2.imencode(".png",vis)[1].tofile(os.path.join(ROOT,"out","overlay","l0_wall.png"))
cv2.imencode(".png",wall)[1].tofile(os.path.join(ROOT,"out","overlay","l0_wallmask.png"))
