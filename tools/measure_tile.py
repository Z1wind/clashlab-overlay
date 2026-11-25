# -*- coding: utf-8 -*-
# 最大档 tile_px 实测：① 草地 2D 自相关找格周期；② 城墙段沿x步长。纯读帧计算。
import cv2, numpy as np, os
OUT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay"
img = cv2.imdecode(np.fromfile(os.path.join(OUT, "v6_zoom_max_raw.png"), dtype=np.uint8), cv2.IMREAD_COLOR)
g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)

# ① 左侧开阔草地自相关（避开建筑/墙）
crop = g[200:560, 40:320]
crop = crop - crop.mean()
f = np.fft.rfft2(crop)
ac = np.fft.irfft2(np.abs(f)**2, s=crop.shape)
ac = np.fft.fftshift(ac)
h, w = ac.shape
ac0 = ac[h//2, w//2]
# 在中心环外找前 6 个峰（排除 DC 邻域 12px）
# 简单局部极大：3x3 邻域最大
mx = cv2.dilate(ac, np.ones((9, 9), np.float32))
ys, xs = np.where((ac == mx) & (ac > ac0*0.05))
d = np.hypot(ys-h//2, xs-w//2)
sel = (d > 12)
ys, xs, d = ys[sel], xs[sel], d[sel]
order = np.argsort(-ac[ys, xs])[:8]
print("=== 自相关峰 (dx,dy, d, val) ===")
for i in order:
    print(f"dx={xs[i]-w//2:+4d} dy={ys[i]-h//2:+4d} d={d[i]:.1f} val={ac[ys[i],xs[i]]/ac0:.3f}")

# ② 输出带 10px 细网格的左侧裁图供目校
vis = img.copy()
for x in range(0, 1280, 10):
    cv2.line(vis, (x, 0), (x, 720), (0, 180, 0), 1)
for y in range(0, 720, 10):
    cv2.line(vis, (0, y), (1280, y), (0, 180, 0), 1)
c = vis[0:620, 0:520]
cv2.imencode(".png", cv2.resize(c, None, fx=1.6, fy=1.6, interpolation=cv2.INTER_NEAREST))[1].tofile(os.path.join(OUT, "v6_tile_grid_left.png"))
print("saved v6_tile_grid_left.png")
