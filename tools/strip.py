# -*- coding: utf-8 -*-
# 金仓石板中腰条带：灰板(V70-195,S<60)逐行左右端点，排除棕色木桶
import cv2, numpy as np, os
D=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\ladder"
img=cv2.imdecode(np.fromfile(os.path.join(D,"m5.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
hsv=cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
H,S,V=cv2.split(hsv)
grey=((S<60)&(V>=70)&(V<=195))
ws=[]
for y in range(500,565,5):
    row=grey[y,300:600]
    xs=np.where(row)[0]
    if len(xs)>20:
        L,R=300+xs.min(),300+xs.max()
        print(f"y={y} L={L} R={R} W={R-L}")
        ws.append(R-L)
print("median W=",float(np.median(ws)) if ws else None)
