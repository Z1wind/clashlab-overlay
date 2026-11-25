# -*- coding: utf-8 -*-
# 全档位相对L0尺度：每帧自动选3个中心块匹配，中位s -> tile_px=24/s
import cv2, numpy as np, os, glob
D=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\ladder"
l0=cv2.imdecode(np.fromfile(os.path.join(D,"zoom_L0.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
files=sorted(glob.glob(os.path.join(D,"zoom_L*.png")),key=lambda p:int(p.split("L")[-1].split(".")[0]))
for f in files:
    img=cv2.imdecode(np.fromfile(f,dtype=np.uint8),cv2.IMREAD_COLOR)
    h,w=img.shape[:2]
    boxes=[(h//2-90,h//2+90,w//2-110,w//2+110),
           (h//4-70,h//4+70,w//3-90,w//3+90),
           (300,460,w//2-130,w//2+90)]
    scs=[];cors=[]
    for (y1,y2,x1,x2) in boxes:
        tpl=img[y1:y2,x1:x2]
        best=None
        for s in np.arange(0.08,0.7,0.005):
            th,tw=max(8,int(tpl.shape[0]*s)),max(8,int(tpl.shape[1]*s))
            small=cv2.resize(tpl,(tw,th),interpolation=cv2.INTER_AREA)
            if th>l0.shape[0] or tw>l0.shape[1]: continue
            res=cv2.matchTemplate(l0,small,cv2.TM_CCOEFF_NORMED)
            _,mv,_,_=cv2.minMaxLoc(res)
            if best is None or mv>best[0]: best=(mv,s)
        if best and best[0]>0.7: scs.append(best[1]);cors.append(best[0])
    name=os.path.basename(f)
    if scs:
        m=float(np.median(scs))
        print(f"{name}: n={len(scs)} corr~{np.mean(cors):.2f} s={m:.3f} tile_px={24/m:.1f} 可见列≈{1280/(24/m):.1f}")
    else:
        print(f"{name}: 无高置信匹配")
