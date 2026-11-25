# -*- coding: utf-8 -*-
# 已知占地建筑底座裁图：散射炮(2x2)、金仓、左上柱，带20px刻度
import cv2, numpy as np, os
OUT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay"
img = cv2.imdecode(np.fromfile(os.path.join(OUT,"v6_zoom_max_raw.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
def crop(name,x1,y1,x2,y2,scale=2.0):
    c=img[y1:y2,x1:x2].copy()
    for x in range(0,x2-x1,20):
        cv2.line(c,(x,0),(x,y2-y1),(0,180,0),1)
        cv2.putText(c,str(x1+x),(x+1,10),cv2.FONT_HERSHEY_SIMPLEX,0.35,(0,255,0),1)
    for y in range(0,y2-y1,20):
        cv2.line(c,(0,y),(x2-x1,y),(0,180,0),1)
        cv2.putText(c,str(y1+y),(1,y+10),cv2.FONT_HERSHEY_SIMPLEX,0.35,(0,255,0),1)
    cv2.imencode(".png",cv2.resize(c,None,fx=scale,fy=scale,interpolation=cv2.INTER_CUBIC))[1].tofile(os.path.join(OUT,f"v6_base_{name}.png"))
crop("scatter",430,590,720,720,1.8)
crop("goldstore",760,480,1020,660,1.8)
crop("pillar",180,110,340,260,2.2)
print("ok")
