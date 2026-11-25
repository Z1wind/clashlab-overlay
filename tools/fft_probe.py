# -*- coding: utf-8 -*-
# 草地窗 FFT 径向主峰周期（20-220px），离线
import cv2, numpy as np, os, sys
D=r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\ladder"
img=cv2.imdecode(np.fromfile(os.path.join(D,sys.argv[1]),dtype=np.uint8),cv2.IMREAD_COLOR)
g=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY).astype(np.float32)
H,W=g.shape
best=[]
for (x,y) in [(560,300),(600,420),(520,180),(820,300),(300,480)]:
    w=g[y:y+160,x:x+160]
    win=np.outer(np.hanning(w.shape[0]),np.hanning(w.shape[1]))
    F=np.fft.fftshift(np.abs(np.fft.fft2(w*win)))
    cy,cx=80,80; F[cy-3:cy+4,cx-3:cx+4]=0
    rad=np.bincount(np.hypot(*np.nonzero(F)).astype(int),F[F>0] if False else F[F>0]) if False else None
    yy,xx=np.nonzero(F)
    rr=np.hypot(yy-80,xx-80).astype(int)
    prof=np.bincount(rr,weights=F[yy,xx],minlength=110)
    prof[:20]=0; prof[100:]=0
    k=int(np.argmax(prof))
    best.append((x,y,160/k if k>0 else None,float(prof[k])))
for b in best: print(b)
