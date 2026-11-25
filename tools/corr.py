# -*- coding: utf-8 -*-
# 两帧相位相关：b 相对 a 的位移 (dx,dy)，报告 response；离线
import cv2, numpy as np, os, sys
D=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\ladder"
def load(n):
    return cv2.imdecode(np.fromfile(os.path.join(D,n),dtype=np.uint8),cv2.IMREAD_COLOR)
a,b=load(sys.argv[1]),load(sys.argv[2])
ga=cv2.cvtColor(a,cv2.COLOR_BGR2GRAY).astype(np.float64)
gb=cv2.cvtColor(b,cv2.COLOR_BGR2GRAY).astype(np.float64)
# 裁 UI 条带后再相关
ga=ga[80:630,155:1105]; gb=gb[80:630,155:1105]
win=cv2.createHanningWindow((ga.shape[1],ga.shape[0]),cv2.CV_64F)
(dx,dy),resp=cv2.phaseCorrelate(ga,gb,win)
print(f"b相对a dx={dx:.2f} dy={dy:.2f} resp={resp:.3f}")
