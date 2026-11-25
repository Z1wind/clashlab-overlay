# -*- coding: utf-8 -*-
# v14_overlay.py — 人工 quad 叠加校验。新文件。
import os, cv2, numpy as np
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
EN = os.path.join(ROOT, "out", "overlay", "enemy")
im = cv2.imdecode(np.fromfile(os.path.join(EN,"b14_ov1.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
T=(640,58); R=(1105,325); B=(640,600); L=(167,308)
pts=np.array([T,R,B,L],np.int32)
cv2.polylines(im,[pts],True,(0,0,255),2)
for nm,p in [("T",T),("R",R),("B",B),("L",L)]:
    cv2.circle(im,p,7,(0,255,255),-1)
    cv2.putText(im,f"{nm}{p}",(p[0]+10,p[1]-10),cv2.FONT_HERSHEY_SIMPLEX,0.6,(0,255,255),2)
cv2.imencode(".png",im)[1].tofile(os.path.join(EN,"b14_quad_check.png"))
W=R[0]-L[0]; H=B[1]-T[1]
print("W",W,"H",H,"W/H",round(W/H,3))
