# -*- coding: utf-8 -*-
# asset_measure.py — tile_px 独立复测：金仓底面 W/3 + 墙帽间距（带 10px 网格）
import os, cv2, numpy as np
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(ROOT, "tools", "base_out", "asset_zoom")
os.makedirs(OUT, exist_ok=True)

def load(p):
    return cv2.imdecode(np.fromfile(os.path.join(ROOT, p), dtype=np.uint8), cv2.IMREAD_COLOR)

def save(c, tag):
    ok, buf = cv2.imencode(".png", c)
    buf.tofile(os.path.join(OUT, tag + ".png"))

im = load(r"out\overlay\ladder\maxzoom_building.png")
# 金仓底 Plinth 区（原图坐标）
c = im[430:600, 260:640].copy()
c = cv2.resize(c, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
for x in range(0, c.shape[1], 20):
    cv2.line(c, (x, 0), (x, c.shape[0]), (0, 255, 255), 1)
for y in range(0, c.shape[0], 20):
    cv2.line(c, (0, y), (c.shape[1], y), (0, 255, 255), 1)
save(c, "measure_goldstore")
# NE 斜墙带（白帽）
c = im[120:360, 660:1160].copy()
c = cv2.resize(c, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
for x in range(0, c.shape[1], 20):
    cv2.line(c, (x, 0), (x, c.shape[0]), (0, 255, 255), 1)
for y in range(0, c.shape[0], 20):
    cv2.line(c, (0, y), (c.shape[1], y), (0, 255, 255), 1)
save(c, "measure_wallcap")
print("done")
