# -*- coding: utf-8 -*-
# 精确：顶部干净墙段 (335,5)->(480,165)，黄顶帽掩膜沿墙投影，报中心距
import cv2, numpy as np, os
OUT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay"
img = cv2.imdecode(np.fromfile(os.path.join(OUT,"v6_zoom_max_raw.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
H,W=img.shape[:2]
b,g,r=cv2.split(img)
cap=((r>200)&(g>160)&(b<120)).astype(np.uint8)  # 黄顶帽
P0=np.array([335.0,5.0]); P1=np.array([480.0,165.0])
d=P1-P0; L=np.hypot(*d); u=d/L; n=np.array([-u[1],u[0]])
prof=np.zeros(int(L))
for s in range(int(L)):
    c=P0+u*s; band=0
    for t in range(-14,15,2):
        p=c+n*t; xi,yi=int(round(p[0])),int(round(p[1]))
        if 0<=xi<W and 0<=yi<H: band+=cap[yi,xi]
    prof[s]=band
ps=np.convolve(prof,np.ones(7)/7,'same')
peaks=[]
for s in range(12,int(L)-12):
    if ps[s]>=ps[s-1] and ps[s]>ps[s+1] and ps[s]>ps.max()*0.4:
        if not peaks or s-peaks[-1]>=25: peaks.append(s)
print("L=%.0f 方向u=(%.3f,%.3f)"%(L,u[0],u[1]))
print("peaks s:",peaks)
sp=np.diff(peaks)
print("段间距:",sp,"均值=%.2f 中位=%.2f"%(sp.mean(),np.median(sp)))
for a,bv in zip(peaks[:-1],peaks[1:]):
    pa=P0+u*a; pb=P0+u*bv
    print(f"  {a}->{bv}: dx={pb[0]-pa[0]:.1f} dy={pb[1]-pa[1]:.1f} |v|={bv-a:.1f}")
vis=img.copy()
for s in peaks:
    c=P0+u*s; cv2.circle(vis,tuple(c.astype(int)),9,(0,0,255),2)
cv2.imencode(".png",vis)[1].tofile(os.path.join(OUT,"v6_wall_precise.png"))
