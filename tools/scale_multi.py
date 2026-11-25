# -*- coding: utf-8 -*-
# 多模板缩放匹配：每档取3个特征块，中位数 scale -> tile_px=24/scale；画框验证
import cv2, numpy as np, os
D=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\ladder"
l0=cv2.imdecode(np.fromfile(os.path.join(D,"zoom_L0.png"),dtype=np.uint8),cv2.IMREAD_COLOR)

def best_scale(frame, boxes, tag):
    scs=[]
    for (y1,y2,x1,x2) in boxes:
        tpl=frame[y1:y2,x1:x2]
        best=None
        for s in np.arange(0.08,0.7,0.005):
            th,tw=max(8,int(tpl.shape[0]*s)),max(8,int(tpl.shape[1]*s))
            small=cv2.resize(tpl,(tw,th),interpolation=cv2.INTER_AREA)
            if th>l0.shape[0] or tw>l0.shape[1]: continue
            res=cv2.matchTemplate(l0,small,cv2.TM_CCOEFF_NORMED)
            _,mv,_,ml=cv2.minMaxLoc(res)
            if best is None or mv>best[0]: best=(mv,s,ml,tw,th)
        if best and best[0]>0.7:
            scs.append(best[1])
            print(f"{tag} 块{boxes.index((y1,y2,x1,x2))}: corr={best[0]:.3f} s={best[1]:.3f} loc={best[2]} tile=%.1f"%(24/best[1]))
    if scs:
        m=float(np.median(scs))
        print(f"{tag} 中位 s={m:.3f} -> tile_px={24/m:.1f}")

l1=cv2.imdecode(np.fromfile(os.path.join(D,"zoom_L1.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
l3=cv2.imdecode(np.fromfile(os.path.join(D,"zoom_L3.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
best_scale(l1,[(250,430,300,480),(120,260,600,760),(380,540,760,920)],"L1")
best_scale(l3,[(380,560,150,360),(60,220,430,620),(300,470,480,660)],"L3")
