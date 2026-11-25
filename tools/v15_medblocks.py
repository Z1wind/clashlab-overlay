# -*- coding: utf-8 -*-
# v15_medblocks.py — max/raw_c{r}c{a/b}.png 双帧中值 -> max/b_c{c}r{r}.png。新文件。
import os, cv2, numpy as np
R = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\_recon"
M = os.path.join(R,"max")
done=0
for r in range(0,9):
    for c in range(0,6):
        fa=os.path.join(M,f"raw_c{c}r{r}_a.png")
        fb=os.path.join(M,f"raw_c{c}r{r}_b.png")
        if not (os.path.exists(fa) and os.path.exists(fb)): continue
        a=cv2.imdecode(np.fromfile(fa,dtype=np.uint8),1)
        b=cv2.imdecode(np.fromfile(fb,dtype=np.uint8),1)
        if a.shape!=b.shape:
            b=cv2.resize(b,(a.shape[1],a.shape[0]))
        med=np.median(np.stack([a,b],0),0).astype(np.uint8)
        out=os.path.join(M,f"b_c{c}r{r}.png")
        cv2.imencode(".png",med)[1].tofile(out)
        done+=1
print("median blocks:",done)
