# -*- coding: utf-8 -*-
# asset_crop.py — 任意区域放大裁剪，供人工点数/测距
import os, sys, cv2, numpy as np
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(ROOT, "tools", "base_out", "asset_zoom")
os.makedirs(OUT, exist_ok=True)

def load(p):
    return cv2.imdecode(np.fromfile(os.path.join(ROOT, p), dtype=np.uint8), cv2.IMREAD_COLOR)

# args: image x0 y0 x1 y1 scale tag
img = load(sys.argv[1])
x0, y0, x1, y1 = [int(v) for v in sys.argv[2:6]]
sc = float(sys.argv[6]); tag = sys.argv[7]
c = img[y0:y1, x0:x1]
c = cv2.resize(c, None, fx=sc, fy=sc, interpolation=cv2.INTER_CUBIC)
# 10px 原坐标网格（放大后 10*sc）
step = int(10*sc)
for x in range(0, c.shape[1], step):
    cv2.line(c, (x, 0), (x, c.shape[0]), (0, 255, 255), 1)
for y in range(0, c.shape[0], step):
    cv2.line(c, (0, y), (c.shape[1], y), (0, 255, 255), 1)
ok, buf = cv2.imencode(".png", c)
buf.tofile(os.path.join(OUT, tag + ".png"))
print("saved", tag, c.shape)
