# -*- coding: utf-8 -*-
# v15_tight.py — 紧裁+10px主线标注，便于读数。新文件。
import os, cv2, numpy as np, sys
R = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\_recon"
src, pref = sys.argv[1], sys.argv[2]
scale = float(sys.argv[3])
im = cv2.imdecode(np.fromfile(os.path.join(R,src),dtype=np.uint8),cv2.IMREAD_COLOR)
for i,arg in enumerate(sys.argv[4:]):
    x1,y1,x2,y2=[int(v) for v in arg.split(",")]
    c=im[y1:y2,x1:x2].copy()
    for x in range(0,c.shape[1]+1,10):
        cv2.line(c,(x,0),(x,c.shape[0]),(0,255,255),1)
        cv2.putText(c,str(x1+x),(x+1,12),cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,255,255),1)
    for y in range(0,c.shape[0]+1,10):
        cv2.line(c,(0,y),(c.shape[1],y),(0,255,255),1)
        cv2.putText(c,str(y1+y),(2,y+10),cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,255,255),1)
    c=cv2.resize(c,None,fx=scale,fy=scale,interpolation=cv2.INTER_NEAREST)
    cv2.imencode(".png",c)[1].tofile(os.path.join(R,f"{pref}_t{i}.png"))
print("ok")
