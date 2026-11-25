# -*- coding: utf-8 -*-
import cv2, numpy as np, os
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
A=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","l0_A.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
for name,(x,y,w,h) in {"green_eagle":(669,465,85,85),"red_TH":(853,430,85,85)}.items():
    c=A[y:y+h,x:x+w]
    c=cv2.resize(c,None,fx=4,fy=4,interpolation=cv2.INTER_CUBIC)
    cv2.imencode(".png",c)[1].tofile(os.path.join(ROOT,"out","overlay",f"box_{name}.png"))
print("ok")
