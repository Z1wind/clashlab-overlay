# -*- coding: utf-8 -*-
# 画布24px网格叠加 + 四象限2x放大，供目读边界点
import cv2, numpy as np, os
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
im=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","v6_l0_two_shot_base.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
h,w=im.shape[:2]
g=im.copy()
for x in range(0,w,24):
    cv2.line(g,(x,0),(x,h),(0,0,255),1)
    if x%120==0: cv2.putText(g,str(x),(x+2,14),cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,0,255),1)
for y in range(0,h,24):
    cv2.line(g,(0,y),(w,y),(0,0,255),1)
    if y%120==0: cv2.putText(g,str(y),(2,y+12),cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,0,255),1)
cv2.imencode(".png",g)[1].tofile(os.path.join(ROOT,"out","overlay","l0new","canvas_grid.png"))
quads={"q_NW":(0,0,500,400),"q_NE":(450,0,950,400),"q_SW":(0,360,500,773),"q_SE":(450,360,950,773)}
for name,(x0,y0,x1,y1) in quads.items():
    c=cv2.resize(g[y0:y1,x0:x1],None,fx=2,fy=2,interpolation=cv2.INTER_CUBIC)
    cv2.imencode(".png",c)[1].tofile(os.path.join(ROOT,"out","overlay","l0new",name+".png"))
print("done",w,h)
