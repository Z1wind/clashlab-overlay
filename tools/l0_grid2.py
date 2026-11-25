# -*- coding: utf-8 -*-
# zoom_L0 参考帧 10px 坐标网格，供目读建筑模板位置
import cv2, numpy as np, os
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
l0=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","ladder","zoom_L0.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
g=l0[80:630,155:1060].copy()
h,w=g.shape[:2]
for x in range(0,w,50):
    cv2.line(g,(x,0),(x,h),(0,0,255),1)
    cv2.putText(g,str(x),(x+2,14),cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,0,255),1)
for y in range(0,h,50):
    cv2.line(g,(0,y),(w,y),(0,0,255),1)
    cv2.putText(g,str(y),(2,y+12),cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,0,255),1)
cv2.imencode(".png",g)[1].tofile(os.path.join(ROOT,"out","overlay","l0_ref_grid.png"))
print(g.shape)
