# -*- coding: utf-8 -*-
# 顶部干净 NE 墙段投影计数：P0(335,5)->P1(640,305)
import cv2, numpy as np, os
OUT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay"
img = cv2.imdecode(np.fromfile(os.path.join(OUT,"v6_zoom_max_raw.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
H,W=img.shape[:2]
b,g,r=cv2.split(img)
# 墙块：奶油白+黄顶，R,G 高 B 中低
wall=((r>170)&(g>140)&(b<170)).astype(np.uint8)
P0=np.array([335.0,5.0]); P1=np.array([640.0,305.0])
d=P1-P0; L=np.hypot(*d); u=d/L; n=np.array([-u[1],u[0]])
prof=np.zeros(int(L))
for s in range(int(L)):
    c=P0+u*s; band=0
    for t in range(-20,21,2):
        p=c+n*t; xi,yi=int(round(p[0])),int(round(p[1]))
        if 0<=xi<W and 0<=yi<H: band+=wall[yi,xi]
    prof[s]=band
ps=np.convolve(prof,np.ones(11)/11,'same')
# 打印 profile 每20s
for s in range(0,int(L),20):
    print(f"s={s:3d} prof={ps[s]:.0f}")
# 峰：局部极大，间距>=35
peaks=[]
for s in range(20,int(L)-20):
    if ps[s]>=ps[s-2] and ps[s]>ps[s+2] and ps[s]>ps.max()*0.45:
        if not peaks or s-peaks[-1]>=35: peaks.append(s)
print("peaks:",peaks)
if len(peaks)>=2:
    sp=np.diff(peaks); print("spacing:",sp,"mean=%.2f med=%.2f"%(sp.mean(),np.median(sp)))
vis=img.copy()
for s in peaks:
    c=P0+u*s; cv2.circle(vis,tuple(c.astype(int)),10,(0,0,255),2)
cv2.imencode(".png",vis)[1].tofile(os.path.join(OUT,"v6_wall_top_peaks.png"))
print("ok")
