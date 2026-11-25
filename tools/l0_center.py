# -*- coding: utf-8 -*-
import cv2, numpy as np, os
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
l0=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","ladder","zoom_L0.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
g=l0[80:630,155:1060]
c=cv2.resize(g[180:400,330:620],None,fx=3,fy=3,interpolation=cv2.INTER_CUBIC)
cv2.imencode(".png",c)[1].tofile(os.path.join(ROOT,"out","overlay","l0_center.png"))
print("ok")
