# -*- coding: utf-8 -*-
# A/B 象限放大供选模板盒
import cv2, numpy as np, os
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT=os.path.join(ROOT,"out","overlay","l0new")
for f in ["A","B"]:
    im=cv2.imdecode(np.fromfile(os.path.join(OUT,f+".png"),dtype=np.uint8),cv2.IMREAD_COLOR)
    h,w=im.shape[:2]
    for name,(x0,y0,x1,y1) in {"TL":(0,0,480,280),"TR":(470,0,950,280),"BL":(0,270,480,550),"BR":(470,270,950,550)}.items():
        q=cv2.resize(im[y0:y1,x0:x1],None,fx=2,fy=2,interpolation=cv2.INTER_CUBIC)
        cv2.imencode(".png",q)[1].tofile(os.path.join(OUT,f+"_"+name+".png"))
print("ok")
