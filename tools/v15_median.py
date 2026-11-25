# -*- coding: utf-8 -*-
# v15_median.py — 三帧逐像素中值，抹粒子留建筑。新文件。
import os, cv2, numpy as np
R = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\_recon"
fs=["recon_default.png","recon_frame_2.png","recon_frame_3.png"]
st=[]
for f in fs:
    im=cv2.imdecode(np.fromfile(os.path.join(R,f),dtype=np.uint8),1)
    st.append(im)
stack=np.stack(st,axis=0)
med=np.median(stack,axis=0).astype(np.uint8)
cv2.imencode(".png",med)[1].tofile(os.path.join(R,"recon_median.png"))
print(med.shape, os.path.getsize(os.path.join(R,"recon_median.png")))
