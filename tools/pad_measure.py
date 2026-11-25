# -*- coding: utf-8 -*-
# 程序化量底座：金顶柱(疑1x1) 红环/白体包围盒；散射炮(2x2) 黄pad包围盒
import cv2, numpy as np, os
OUT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay"
img = cv2.imdecode(np.fromfile(os.path.join(OUT,"v6_zoom_max_raw.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
b,g,r=cv2.split(img)

def bbox(mask, name):
    ys,xs=np.where(mask)
    if len(xs)==0: print(name,"空"); return
    print(f"{name}: x {xs.min()}..{xs.max()} (W={xs.max()-xs.min()}), y {ys.min()}..{ys.max()} (H={ys.max()-ys.min()})")

# 金顶柱1 区域 (180,110,340,260)
x1,y1,x2,y2=180,110,340,260
red=((r>120)&(g<90)&(b<90))[y1:y2,x1:x2]
white=((r>190)&(g>190)&(b>180))[y1:y2,x1:x2]
bbox(red,"柱1红环")
bbox(white,"柱1白体")

# 柱2 (180,390,340,540)
y1,y2=390,540
red2=((r>120)&(g<90)&(b<90))[y1:y2,x1:x2]
white2=((r>190)&(g>190)&(b>180))[y1:y2,x1:x2]
bbox(red2,"柱2红环")
bbox(white2,"柱2白体")

# 散射炮 2x2 区域 (640,560,860,720) 黄pad
x1,y1,x2,y2=640,560,880,720
yellow=((r>180)&(g>140)&(b<110))[y1:y2,x1:x2]
bbox(yellow,"散射黄pad")
