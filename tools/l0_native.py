# -*- coding: utf-8 -*-
# 纯离线：在原生全帧 s1_full 上裁候选建筑放大，判断原生分辨率是否可辨底面
import cv2, numpy as np, os
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
for f in ["s1_full.png","s2_full.png","s3_full.png"]:
    p=os.path.join(ROOT,"out","overlay","l0three",f)
    im=cv2.imdecode(np.fromfile(p,dtype=np.uint8),cv2.IMREAD_COLOR)
    print(f,im.shape)
