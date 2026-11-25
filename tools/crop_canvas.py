# -*- coding: utf-8 -*-
# 裁拼接图局部供目检: crop_canvas.py x1 y1 x2 y2 out
import cv2, numpy as np, os, sys
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
im=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","v6_stitched_base.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
x1,y1,x2,y2=map(int,sys.argv[2:6])
c=im[y1:y2,x1:x2]
sc=float(sys.argv[6]) if len(sys.argv)>6 else 1.0
cv2.imencode(".png",cv2.resize(c,None,fx=sc,fy=sc,interpolation=cv2.INTER_CUBIC))[1].tofile(os.path.join(ROOT,"out","overlay",sys.argv[1]))
print("ok",c.shape)
