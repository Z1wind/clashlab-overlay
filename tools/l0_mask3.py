# -*- coding: utf-8 -*-
# v3分割：平台草 V高 S中；森林V低；调阈值看mask
import cv2, numpy as np, os
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
im=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","v6_l0_two_shot_base.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
for tag,lo,hi in [("a",(28,30,165),(95,170,255)),("b",(28,30,175),(95,160,255)),("c",(30,40,180),(90,150,255))]:
    m=cv2.inRange(hsv,np.array(lo),np.array(hi))
    m[hsv[:,:,0]>95]=0
    m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((25,25),np.uint8))
    cnts,_=cv2.findContours(m,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    cnt=max(cnts,key=cv2.contourArea)
    fill=np.zeros_like(m); cv2.drawContours(fill,[cnt],-1,255,-1)
    cv2.imencode(".png",fill)[1].tofile(os.path.join(ROOT,"out","overlay","l0new",f"mask3_{tag}.png"))
    print(tag,"area=",cv2.contourArea(cnt))
