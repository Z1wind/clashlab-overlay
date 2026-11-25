# -*- coding: utf-8 -*-
import cv2, numpy as np, os
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
P=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","v6_L0_pair_stitched.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
for name,(x,y,w,h) in {"AD_blue":(818,557,75,60),"Gold_yellow":(711,528,74,70),"Wiz_mag":(808,528,75,70)}.items():
    c=P[y:y+h,x:x+w]
    c=cv2.resize(c,None,fx=4,fy=4,interpolation=cv2.INTER_CUBIC)
    cv2.imencode(".png",c)[1].tofile(os.path.join(ROOT,"out","overlay",f"box_{name}.png"))
print("ok")
