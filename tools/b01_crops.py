# -*- coding: utf-8 -*-
"""直接看 b01 的几个标注裁剪（放大幅面）。"""
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab.geo import Calib
DL = os.path.join(os.path.expanduser("~"), "Downloads")
d = json.load(open(os.path.join(DL, "annot_b01.json"), encoding="utf-8"))
img = cv2.imdecode(np.fromfile(os.path.join(BASE, "android", "assets", "img", "b01.jpg"), np.uint8), cv2.IMREAD_COLOR)
wn, hn = d["image_size"]; quad = np.float32([[u*wn, v*hn] for u, v in d["corners_norm"]])
cal = Calib.from_quad(quad, n=44)
picks = d["buildings"][:8]
tiles = []
for b in picks:
    x, y = b["tile"]; side = 4
    x0 = max(0, x-2); y0 = max(0, y-2); x1 = min(44, x0+side); y1 = min(44, y0+side)
    p = [cal.tile_to_px(x0,y0), cal.tile_to_px(x1,y0), cal.tile_to_px(x1,y1), cal.tile_to_px(x0,y1)]
    H = cv2.getPerspectiveTransform(np.float32(p), np.float32([[0,0],[120,0],[120,120],[0,120]]))
    c = cv2.warpPerspective(img, H, (120,120))
    cv2.putText(c, b["type"][:12], (2, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0,255,255), 1)
    tiles.append(c); print(b["type"], b["tile"])
rows = [np.hstack(tiles[i:i+4]) for i in range(0, len(tiles), 4)]
canvas = np.vstack(rows)
cv2.imencode(".png", canvas)[1].tofile(os.path.join(BASE, "out", "apk_qa", "b01_crops8.png"))
print("saved b01_crops8.png", canvas.shape)
