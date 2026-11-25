# -*- coding: utf-8 -*-
# v15_diffmap.py — 差异热点定位：阈值二值化，列/行投影，存差异图。新文件。
import os, cv2, numpy as np
R = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\_recon"
a = cv2.imdecode(np.fromfile(os.path.join(R,"recon_default.png"),dtype=np.uint8),1)
b = cv2.imdecode(np.fromfile(os.path.join(R,"recon_frame_2.png"),dtype=np.uint8),1)
d = cv2.absdiff(a,b); g = cv2.cvtColor(d,cv2.COLOR_BGR2GRAY)
_,th = cv2.threshold(g,25,255,cv2.THRESH_BINARY)
vis = a.copy(); vis[th>0]=(0,0,255)
cv2.imencode(".png",vis)[1].tofile(os.path.join(R,"diffmap_12.png"))
# 连通域
n,lab,stats,cent = cv2.connectedComponentsWithStats(th)
big = sorted([(stats[i,4],stats[i,:4].tolist()) for i in range(1,n)],reverse=True)[:12]
for area,box in big: print(area,box)
