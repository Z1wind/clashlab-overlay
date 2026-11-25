# -*- coding: utf-8 -*-
# asset_zoom.py — 切象限放大图，供人工点数（只读输入，写 tools/base_out）
import os, cv2, numpy as np
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(ROOT, "tools", "base_out", "asset_zoom")
os.makedirs(OUT, exist_ok=True)

def load(p):
    return cv2.imdecode(np.fromfile(os.path.join(ROOT, p), dtype=np.uint8), cv2.IMREAD_COLOR)

def save(im, name):
    ok, buf = cv2.imencode(".png", im)
    buf.tofile(os.path.join(OUT, name))

# b14_full 四象限 2x
im = load(r"out\overlay\enemy\b14_full.png")
H, W = im.shape[:2]
print("b14_full", W, H)
quads = {
    "b14_q_tl": (0, 0, W//2, H//2),
    "b14_q_tr": (W//2, 0, W, H//2),
    "b14_q_bl": (0, H//2, W//2, H),
    "b14_q_br": (W//2, H//2, W, H),
}
for name, (x0, y0, x1, y1) in quads.items():
    c = im[y0:y1, x0:x1]
    c = cv2.resize(c, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    # 画网格参考线（原像素每20px）
    for x in range(0, c.shape[1], 40):
        cv2.line(c, (x, 0), (x, c.shape[0]), (0, 255, 255), 1)
    for y in range(0, c.shape[0], 40):
        cv2.line(c, (0, y), (c.shape[1], y), (0, 255, 255), 1)
    save(c, name + ".png")

# war 14 裁切表面后整图 1.5x
b = load(r"bases\th16\war_20261123\14_kekejdj.png")
L, T, R, B = 15, 35, 1024, 585
c = b[T:B, L:R]
c = cv2.resize(c, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
save(c, "w14_surface.png")
print("w14 surface", c.shape)
