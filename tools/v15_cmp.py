# -*- coding: utf-8 -*-
# v15_cmp.py — 两帧差异概览（min vs median）。新文件。
import os, cv2, numpy as np
R = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\_recon"
a=cv2.imdecode(np.fromfile(os.path.join(R,"recon_median.png"),dtype=np.uint8),1)
b=cv2.imdecode(np.fromfile(os.path.join(R,"recon_zoom_min.png"),dtype=np.uint8),1)
d=cv2.absdiff(a,b);g=cv2.cvtColor(d,cv2.COLOR_BGR2GRAY)
print("min vs median: diff_px=",int(np.count_nonzero(g)),"max=",int(g.max()),"mean=",round(float(g.mean()),3))
