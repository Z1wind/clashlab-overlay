# -*- coding: utf-8 -*-
# m2 金仓(3x3)非草地掩膜外接框；打印bbox，叠加框图
import cv2, numpy as np, os
D=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\ladder"
img=cv2.imdecode(np.fromfile(os.path.join(D,"m2.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
hsv=cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
# 草地绿：H 35-85, S>40, V>60；取反=物体
grass=cv2.inRange(hsv,(35,40,60),(95,255,230))
obj=255-grass
# ROI 金仓 (280,280)-(620,610)
roi=np.zeros_like(obj); roi[280:610,280:620]=obj[280:610,280:620]
roi=cv2.morphologyEx(roi,cv2.MORPH_CLOSE,np.ones((15,15),np.uint8))
n,lab,stats,_=cv2.connectedComponentsWithStats(roi)
vis=img.copy()
for i in range(1,n):
    x,y,w,a=stats[i][0],stats[i][1],stats[i][2],stats[i][4]
    h=stats[i][3]
    if a>3000:
        print(f"组件 x={x} y={y} W={w} H={h} area={a} -> W/3={w/3:.1f}")
        cv2.rectangle(vis,(x,y),(x+w,y+h),(0,0,255),2)
cv2.imencode(".png",vis)[1].tofile(os.path.join(D,"gs_bbox.png"))
