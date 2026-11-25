# -*- coding: utf-8 -*-
# 两区域像素差异（对齐后），判重复粘贴 vs 同类建筑
import cv2, numpy as np, os, sys
ROOT=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
im=cv2.imdecode(np.fromfile(os.path.join(ROOT,"out","overlay","v6_stitched_base.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
# 区域1 (40,40) 区域2 (40,641) 同尺寸 280x240
A=im[40:280,40:320]; B=im[641:881,40:320]
d=np.abs(A.astype(int)-B.astype(int))
print("mean abs diff=",round(d.mean(),1),"p95=",round(np.percentile(d,95),1))
# 灰度结构相似度
ga=cv2.cvtColor(A,cv2.COLOR_BGR2GRAY).astype(np.float32)
gb=cv2.cvtColor(B,cv2.COLOR_BGR2GRAY).astype(np.float32)
cc=cv2.matchTemplate(ga,gb,cv2.TM_CCOEFF_NORMED)[0,0]
print("NCC=",round(float(cc),3))
cv2.imencode(".png",np.hstack([A,B]))[1].tofile(os.path.join(ROOT,"out","overlay","region_ab.png"))
