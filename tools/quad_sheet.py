# -*- coding: utf-8 -*-
# 全帧四象限裁 + 50px 刻度标签，找长直城墙段
import cv2, numpy as np, os
OUT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay"
img = cv2.imdecode(np.fromfile(os.path.join(OUT,"v6_zoom_max_raw.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
H,W = img.shape[:2]
cells = {"tl":(0,0,640,360),"tr":(640,0,1280,360),"bl":(0,360,640,720),"br":(640,360,1280,720)}
for name,(x1,y1,x2,y2) in cells.items():
    c = img[y1:y2,x1:x2].copy()
    for x in range(0,x2-x1,50):
        cv2.line(c,(x,0),(x,y2-y1),(0,180,0),1)
        cv2.putText(c,str(x1+x),(x+2,12),cv2.FONT_HERSHEY_SIMPLEX,0.35,(0,255,0),1)
    for y in range(0,y2-y1,50):
        cv2.line(c,(0,y),(x2-x1,y),(0,180,0),1)
        cv2.putText(c,str(y1+y),(2,y+12),cv2.FONT_HERSHEY_SIMPLEX,0.35,(0,255,0),1)
    cv2.imencode(".png",c)[1].tofile(os.path.join(OUT,f"v6_q_{name}.png"))
print("ok")
