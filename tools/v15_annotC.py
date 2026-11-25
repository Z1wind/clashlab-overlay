# -*- coding: utf-8 -*-
# v15_annotC.py — 通用标注：src pref box... 网格 step，放大。新文件。
import os, cv2, numpy as np, sys
R = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\_recon"
src, pref = sys.argv[1], sys.argv[2]
step = int(sys.argv[3]) if len(sys.argv)>3 else 5
scale = float(sys.argv[4]) if len(sys.argv)>4 else 3.0
im = cv2.imdecode(np.fromfile(os.path.join(R,src),dtype=np.uint8),cv2.IMREAD_COLOR)
def annot(box,name):
    x1,y1,x2,y2=box
    c=im[y1:y2,x1:x2].copy()
    for x in range(0,c.shape[1],step):
        cv2.line(c,(x,0),(x,c.shape[0]),(0,255,255),1)
        cv2.putText(c,str(x1+x),(x+1,11),cv2.FONT_HERSHEY_SIMPLEX,0.32,(0,255,255),1)
    for y in range(0,c.shape[0],step):
        cv2.line(c,(0,y),(c.shape[1],y),(0,255,255),1)
        cv2.putText(c,str(y1+y),(1,y+9),cv2.FONT_HERSHEY_SIMPLEX,0.32,(0,255,255),1)
    c=cv2.resize(c,None,fx=scale,fy=scale,interpolation=cv2.INTER_NEAREST)
    cv2.imencode(".png",c)[1].tofile(os.path.join(R,name))
for i,arg in enumerate(sys.argv[5:]):
    x1,y1,x2,y2=[int(v) for v in arg.split(",")]
    annot((x1,y1,x2,y2),f"{pref}_c{i}.png")
print("ok")
