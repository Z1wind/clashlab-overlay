# -*- coding: utf-8 -*-
# v15_crop.py — 无网格裁块，供人工计数。新文件。
import os, cv2, numpy as np, sys
R = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\_recon"
src, pref = sys.argv[1], sys.argv[2]
scale = float(sys.argv[3])
im = cv2.imdecode(np.fromfile(os.path.join(R,src),dtype=np.uint8),1)
for i,arg in enumerate(sys.argv[4:]):
    x1,y1,x2,y2=[int(v) for v in arg.split(",")]
    c=im[y1:y2,x1:x2]
    c=cv2.resize(c,None,fx=scale,fy=scale,interpolation=cv2.INTER_CUBIC)
    cv2.imencode(".png",c)[1].tofile(os.path.join(R,f"{pref}_q{i}.png"))
print("ok")
