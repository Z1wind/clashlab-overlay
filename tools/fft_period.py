# -*- coding: utf-8 -*-
# 干净草地 FFT 周期图：找主导空间频率 -> 格周期（不依赖2:1假设）
import cv2, numpy as np, os
OUT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay"
img = cv2.imdecode(np.fromfile(os.path.join(OUT,"v6_zoom_max_raw.png"),dtype=np.uint8),cv2.IMREAD_COLOR)
g=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY).astype(np.float64)
PATCHES={
 "p1":(40,300,260,430),
 "p2":(300,300,470,430),
 "p3":(60,60,200,180),
 "p4":(900,360,1080,500),
}
for name,(x1,y1,x2,y2) in PATCHES.items():
    c=g[y1:y2,x1:x2]
    c=c-c.mean()
    # 窗
    wy=np.hanning(c.shape[0])[:,None]; wx=np.hanning(c.shape[1])[None,:]
    c=c*wy*wx
    F=np.fft.fftshift(np.fft.fft2(c))
    h,w=F.shape; cy,cx=h//2,w//2
    M=np.abs(F); M[cy,cx]=0
    # 排除DC 10px环，取前5峰
    yy,xx=np.mgrid[0:h,0:w]
    rr=np.hypot(yy-cy,xx-cx)
    M[rr<12]=0
    flat=M.ravel(); idx=np.argpartition(flat,-5)[-5:]
    print(f"--- {name} ({x2-x1}x{y2-y1}) ---")
    for i in idx:
        y,x=np.divmod(i,w)
        fx=(x-cx)/(x2-x1); fy=(y-cy)/(y2-y1)
        perx=1/abs(fx) if fx else 0; pery=1/abs(fy) if fy else 0
        print(f"  f=({fx:+.4f},{fy:+.4f}) period=({perx:.1f},{pery:.1f}) mag={flat[i]:.0f}")
