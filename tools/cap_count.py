# -*- coding: utf-8 -*-
# L3 底部墙段黄帽投影计数：P0(185,635)->P1(645,400)，报峰位/间距
import cv2, numpy as np, os
D=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\ladder"
img=cv2.imdecode(np.fromfile(os.path.join(D,"zoom_L3.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
H,W=img.shape[:2]; b,g,r=cv2.split(img)
cap=((r>190)&(g>150)&(b<130)).astype(np.uint8)
P0=np.array([185.0,635.0]); P1=np.array([645.0,400.0])
d=P1-P0; L=np.hypot(*d); u=d/L; n=np.array([-u[1],u[0]])
prof=np.zeros(int(L))
for s in range(int(L)):
    c=P0+u*s; band=0
    for t in range(-16,17,2):
        p=c+n*t; xi,yi=int(round(p[0])),int(round(p[1]))
        if 0<=xi<W and 0<=yi<H: band+=cap[yi,xi]
    prof[s]=band
ps=np.convolve(prof,np.ones(9)/9,'same')
peaks=[]
for s in range(15,int(L)-15):
    if ps[s]>=ps[s-1] and ps[s]>ps[s+1] and ps[s]>ps.max()*0.35:
        if not peaks or s-peaks[-1]>=30: peaks.append(s)
print("L=%.0f u=(%.3f,%.3f)"%(L,u[0],u[1]))
print("peaks:",peaks)
sp=np.diff(peaks)
print("间距:",sp,"均值=%.1f 中位=%.1f"%(sp.mean(),np.median(sp)))
for a,bv in zip(peaks[:-1],peaks[1:]):
    pa=P0+u*a; pb=P0+u*bv
    print(f"  {a}->{bv}: dx={pb[0]-pa[0]:.1f} dy={pb[1]-pa[1]:.1f} |v|={bv-a:.1f}")
vis=img.copy()
for s in peaks:
    c=P0+u*s; cv2.circle(vis,tuple(c.astype(int)),10,(0,0,255),2)
cv2.imencode(".png",vis)[1].tofile(os.path.join(D,"caps_L3.png"))
