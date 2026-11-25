# -*- coding: utf-8 -*-
# 行扫描：金仓灰石板在各水平行的非草地左右端点；墙白帽亮斑检测
import cv2, numpy as np, os
D=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\ladder"
img=cv2.imdecode(np.fromfile(os.path.join(D,"m5.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
hsv=cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
H,S,V=cv2.split(hsv)
grass=((H>=35)&(H<=95)&(S>35)&(V>55))
nongrass=~grass
print("== 金仓pad水平行扫描(非草地端点) ROI x300-600 ==")
for y in range(470,590,10):
    row=nongrass[y,300:600]
    xs=np.where(row)[0]
    if len(xs)>0:
        print(f"y={y}: L={300+xs.min()} R={300+xs.max()} W={xs.max()-xs.min()}")
