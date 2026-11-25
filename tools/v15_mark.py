# -*- coding: utf-8 -*-
# v15_mark.py — 在各档帧上圈出测量点存 scale_mark_<档>.png。新文件。
import os, cv2, numpy as np
R = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\_recon"
def mark(src,dst,boxes,texts):
    im=cv2.imdecode(np.fromfile(os.path.join(R,src),dtype=np.uint8),1)
    for (x1,y1,x2,y2),t in zip(boxes,texts):
        cv2.rectangle(im,(x1,y1),(x2,y2),(0,0,255),2)
        cv2.putText(im,t,(x1,y1-6),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,0,255),2)
    cv2.imencode(".png",im)[1].tofile(os.path.join(R,dst))
mark("recon_median.png","scale_mark_default.png",
     [(440,112,760,140),(540,120,670,180)],
     ["wall bay row","dark storage(art溢,弃)"])
mark("recon_zoom_min.png","scale_mark_min.png",
     [(440,112,760,140)],["wall bay row"])
mark("recon_zoom_max.png","scale_mark_max.png",
     [(262,255,482,415),(1030,345,1165,415)],
     ["spell tower 3x3","cannon 2x2"])
print("ok")
