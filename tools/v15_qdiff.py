# -*- coding: utf-8 -*-
# v15_qdiff.py — 象限两帧静止判定。新文件。
import os, cv2, numpy as np, sys
R = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\_recon"
a=cv2.imdecode(np.fromfile(os.path.join(R,sys.argv[1]),dtype=np.uint8),1)
b=cv2.imdecode(np.fromfile(os.path.join(R,sys.argv[2]),dtype=np.uint8),1)
d=cv2.absdiff(a,b);g=cv2.cvtColor(d,cv2.COLOR_BGR2GRAY)
print("diff_px=",int(np.count_nonzero(g)),"max=",int(g.max()),"mean=",round(float(g.mean()),3))
