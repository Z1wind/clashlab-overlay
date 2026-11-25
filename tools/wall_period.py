# -*- coding: utf-8 -*-
# 干净 NE-SW 墙段：黄色顶帽掩膜沿墙投影，找块间距（1格=1墙段）
import cv2, numpy as np, os
OUT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay"
img = cv2.imdecode(np.fromfile(os.path.join(OUT,"v6_zoom_max_raw.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
H,W = img.shape[:2]
b,g,r = cv2.split(img)
yellow = ((r>190)&(g>150)&(b<130)).astype(np.uint8)

# 墙中心线 P0(235,715)->P1(625,435)，方向 d=(390,-280)
P0=np.array([235.0,715.0]); d=np.array([390.0,-280.0]); L=np.hypot(*d); u=d/L; n=np.array([-u[1],u[0]])
prof=np.zeros(int(L))
for s in range(int(L)):
    c = P0+u*s
    band=0
    for t in range(-18,19,3):
        p=c+n*t
        xi,yi=int(round(p[0])),int(round(p[1]))
        if 0<=xi<W and 0<=yi<H: band+=yellow[yi,xi]
    prof[s]=band
# 平滑 + 峰
k=np.ones(9)/9; ps=np.convolve(prof,k,'same')
peaks=[]; min_dist=28
for s in range(15,int(L)-15):
    if ps[s]>ps[s-1] and ps[s]>=ps[s+1] and ps[s]>np.percentile(ps,70):
        if not peaks or s-peaks[-1]>=min_dist:
            peaks.append(s)
print("墙长 L=%.0fpx, 峰位 s:"%L, peaks)
if len(peaks)>=2:
    sp=np.diff(peaks)
    print("段间距(px):", sp, "均值=%.2f 中位=%.2f"%(sp.mean(),np.median(sp)))
    # 墙方向上每格像素长度；水平投影步长 = 均值*u_x, 垂直 = 均值*|u_y|
    print("每格沿墙 %.1f px; 水平投影 %.1f; 垂直投影 %.1f"%(np.median(sp),np.median(sp)*abs(u[0]),np.median(sp)*abs(u[1])))
# 叠加可视化
vis=img.copy()
for s in peaks:
    c=P0+u*s
    cv2.circle(vis,tuple(c.astype(int)),8,(0,0,255),2)
cv2.imencode(".png",vis)[1].tofile(os.path.join(OUT,"v6_wall_peaks.png"))
print("saved v6_wall_peaks.png")
