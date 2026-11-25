# -*- coding: utf-8 -*-
# v15_preview.py — 大图缩小预览。新文件。
import cv2,numpy as np,sys,os
R=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\_recon"
im=cv2.imdecode(np.fromfile(os.path.join(R,sys.argv[1]),dtype=np.uint8),1)
s=1400/im.shape[1]
small=cv2.resize(im,None,fx=s,fy=s,interpolation=cv2.INTER_AREA)
cv2.imencode(".png",small)[1].tofile(os.path.join(R,sys.argv[2]))
print(small.shape)
