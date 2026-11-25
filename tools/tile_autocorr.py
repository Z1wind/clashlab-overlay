# -*- coding: utf-8 -*-
# 多块纯草地 2D 自相关，找小尺度格周期(5-90px)；另输出候选1x1建筑底视裁。
import cv2, numpy as np, os
OUT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay"
img = cv2.imdecode(np.fromfile(os.path.join(OUT, "v6_zoom_max_raw.png"), dtype=np.uint8), cv2.IMREAD_COLOR)
g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)

# 候选草地块（x1,y1,x2,y2），避开建筑
PATCHES = {
 "left_lawn": (60, 320, 230, 520),
 "center_lawn": (300, 320, 470, 520),
 "right_lawn": (760, 360, 960, 560),
 "top_lawn": (300, 20, 500, 150),
}
for name,(x1,y1,x2,y2) in PATCHES.items():
    c = g[y1:y2, x1:x2]
    c = c - c.mean()
    f = np.fft.rfft2(c)
    ac = np.fft.irfft2(np.abs(f)**2, s=c.shape)
    ac = np.fft.fftshift(ac)
    h,w = ac.shape; ac0 = ac[h//2,w//2]
    mx = cv2.dilate(ac, np.ones((7,7),np.float32))
    ys,xs = np.where((ac==mx)&(ac>ac0*0.08))
    d = np.hypot(ys-h//2, xs-w//2)
    sel=(d>=8)&(d<=90)
    ys,xs,d=ys[sel],xs[sel],d[sel]
    if len(xs)==0:
        print(name, "无峰"); continue
    o=np.argsort(-ac[ys,xs])[:6]
    print(f"--- {name} ---")
    for i in o:
        print(f"  dx={xs[i]-w//2:+4d} dy={ys[i]-h//2:+4d} d={d[i]:.1f} v={ac[ys[i],xs[i]]/ac0:.3f}")

# 底部散射炮底座裁图供量 2x2
c = img[560:720, 430:720]
cv2.imencode(".png", cv2.resize(c, None, fx=2.2, fy=2.2, interpolation=cv2.INTER_CUBIC))[1].tofile(os.path.join(OUT,"v6_base_scatter.png"))
print("saved v6_base_scatter.png")
