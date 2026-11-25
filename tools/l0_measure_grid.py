# -*- coding: utf-8 -*-
# 纯离线：三帧画布上画坐标参考网格(24px)与象限放大，供人工读建筑底面
import cv2, numpy as np, os
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
im=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","v6_l0_three_shot_base.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
H,W=im.shape[:2]
print("canvas",W,H)
g=im.copy()
for x in range(0,W,24):
    cv2.line(g,(x,0),(x,H),(0,0,255),1)
    if x%120==0: cv2.putText(g,str(x),(x+2,14),cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,0,255),1)
for y in range(0,H,24):
    cv2.line(g,(0,y),(W,y),(0,0,255),1)
    if y%120==0: cv2.putText(g,str(y),(2,y+12),cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,0,255),1)
cv2.imencode(".png",g)[1].tofile(os.path.join(ROOT,"out","overlay","l0three","refgrid_full.png"))
# 象限放大2x
quads={"q1_TL":(0,0,460,560),"q2_TR":(445,0,905,560),"q3_BL":(0,520,460,1068),"q4_BR":(445,520,905,1068)}
for name,(x0,y0,x1,y1) in quads.items():
    q=cv2.resize(g[y0:y1,x0:x1],None,fx=2,fy=2,interpolation=cv2.INTER_CUBIC)
    cv2.imencode(".png",q)[1].tofile(os.path.join(ROOT,"out","overlay","l0three",name+".png"))
print("done")
