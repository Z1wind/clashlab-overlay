# -*- coding: utf-8 -*-
# asset_cropall.py — 为 4 张 war 表面切放大图；b14 测墙距
import os, cv2, numpy as np
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(ROOT, "tools", "base_out", "asset_zoom")
os.makedirs(OUT, exist_ok=True)

def load(p):
    return cv2.imdecode(np.fromfile(os.path.join(ROOT, p), dtype=np.uint8), cv2.IMREAD_COLOR)

def save(c, tag):
    ok, buf = cv2.imencode(".png", c)
    buf.tofile(os.path.join(OUT, tag + ".png"))

bounds = {
    "w14": (r"bases\th16\war_20261123\14_kekejdj.png", (15, 35, 1024, 585)),
    "w15": (r"bases\th16\war_20261123\15_qembzi.png", (15, 48, 1028, 602)),
    "w16": (r"bases\th16\war_20261123\16_diddieyang.png", (15, 48, 1027, 599)),
    "w17": (r"bases\th16\war_20261123\17_akib.png", (15, 46, 1021, 596)),
}
for tag, (p, (L, T, R, B)) in bounds.items():
    im = load(p)[T:B, L:R]
    h, w = im.shape[:2]
    # 整表面 1.2x + 四象限 2.5x
    full = cv2.resize(im, None, fx=1.2, fy=1.2, interpolation=cv2.INTER_CUBIC)
    save(full, tag + "_full")
    for q, (x0, y0, x1, y1) in {
        "tl": (0, 0, w//2, h//2), "tr": (w//2, 0, w, h//2),
        "bl": (0, h//2, w//2, h), "br": (w//2, h//2, w, h),
    }.items():
        c = im[y0:y1, x0:x1]
        c = cv2.resize(c, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC)
        save(c, f"{tag}_{q}")
# b14 直线墙测距区
im = load(r"out\overlay\enemy\b14_full.png")
save(cv2.resize(im[60:140, 380:560], None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC), "b14_wallN")
save(cv2.resize(im[300:380, 60:240], None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC), "b14_wallW")
print("done")
