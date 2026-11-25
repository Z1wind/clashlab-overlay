# -*- coding: utf-8 -*-
# v15_diff.py — 三帧逐像素比对：差异像素数、最大通道差、均值差。新文件。
import os, cv2, numpy as np, sys
R = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\_recon"
a = cv2.imdecode(np.fromfile(os.path.join(R,"recon_default.png"),dtype=np.uint8),1)
b = cv2.imdecode(np.fromfile(os.path.join(R,"recon_frame_2.png"),dtype=np.uint8),1)
c = cv2.imdecode(np.fromfile(os.path.join(R,"recon_frame_3.png"),dtype=np.uint8),1)
for nm,x,y in [("d12",a,b),("d23",b,c),("d13",a,c)]:
    d = cv2.absdiff(x,y)
    g = cv2.cvtColor(d,cv2.COLOR_BGR2GRAY)
    nz = int(np.count_nonzero(g))
    print(nm, "diff_px=",nz, "max=",int(g.max()), "mean=",round(float(g.mean()),3), "shape=",g.shape)
