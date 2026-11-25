# -*- coding: utf-8 -*-
# 连通分量法量底座：黄/金 pad、红环，只取大分量
import cv2, numpy as np, os
OUT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay"
img = cv2.imdecode(np.fromfile(os.path.join(OUT,"v6_zoom_max_raw.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
b,g,r=cv2.split(img)

def comps(mask, name, minarea=200):
    n,lab,stats,cent=cv2.connectedComponentsWithStats(mask.astype(np.uint8),8)
    out=[]
    for i in range(1,n):
        x,y,w,h,a=stats[i]
        if a>=minarea: out.append((a,x,y,w,h))
    out.sort(reverse=True)
    print(f"--- {name} ---")
    for a,x,y,w,h in out[:8]:
        print(f"  area={a} x={x} y={y} W={w} H={h}")

yellow=((r>180)&(g>140)&(b<120))
comps(yellow,"黄/金(全图)")
red=((r>130)&(g<90)&(b<90))
comps(red,"红环(全图)")
