# -*- coding: utf-8 -*-
import os, cv2, numpy as np
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
EN = os.path.join(ROOT, "out", "overlay", "enemy")
a = cv2.imdecode(np.fromfile(os.path.join(EN,"b14_ov1.png"),dtype=np.uint8),cv2.IMREAD_GRAYSCALE)
g = cv2.imdecode(np.fromfile(os.path.join(EN,"b14_rec.png"),dtype=np.uint8),cv2.IMREAD_GRAYSCALE)
patch = g[180:480,450:830]
res = cv2.matchTemplate(a,patch,cv2.TM_CCOEFF_NORMED)
_,mx,_,ml=cv2.minMaxLoc(res)
print("offset",(ml[0]-450,ml[1]-180),"score",round(mx,3))
