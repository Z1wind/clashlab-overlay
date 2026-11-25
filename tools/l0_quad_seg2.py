# -*- coding: utf-8 -*-
# 平台草地分割v2：放宽阈值+大核闭合+填洞；输出最大外轮廓极值点与debug
import cv2, numpy as np, os
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
im=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","v6_l0_two_shot_base.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
# 平台浅草：宽绿，V较高；排除深林(V<120)、水(蓝)、沙(低S)
mask=cv2.inRange(hsv,np.array([28,25,120]),np.array([95,190,255]))
# 去蓝水
mask[hsv[:,:,0]>95]=0
mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((31,31),np.uint8))
mask=cv2.morphologyEx(mask,cv2.MORPH_OPEN,np.ones((7,7),np.uint8))
cnts,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
cnt=max(cnts,key=cv2.contourArea)
fill=np.zeros_like(mask); cv2.drawContours(fill,[cnt],-1,255,-1)
dbg=im.copy(); cv2.drawContours(dbg,[cnt],-1,(0,0,255),2)
pts=cnt[:,0,:]
iT=np.argmin(pts[:,1]); iB=np.argmax(pts[:,1]); iL=np.argmin(pts[:,0]); iR=np.argmax(pts[:,0])
for name,i,col in [("T",iT,(0,255,0)),("B",iB,(255,0,0)),("L",iL,(0,255,255)),("R",iR,(255,0,255))]:
    x,y=pts[i]; cv2.circle(dbg,(x,y),8,col,-1); cv2.putText(dbg,f"{name}({x},{y})",(x+10,y),cv2.FONT_HERSHEY_SIMPLEX,0.6,col,2)
print("area=",cv2.contourArea(cnt),"T",tuple(pts[iT]),"B",tuple(pts[iB]),"L",tuple(pts[iL]),"R",tuple(pts[iR]))
cv2.imencode(".png",dbg)[1].tofile(os.path.join(ROOT,"out","overlay","l0new","quad_debug2.png"))
cv2.imencode(".png",fill)[1].tofile(os.path.join(ROOT,"out","overlay","l0new","mask2.png"))
