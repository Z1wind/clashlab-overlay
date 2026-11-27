# -*- coding: utf-8 -*-
"""偏移对比：GT 大本营 (16,16) 在 4 种偏移下的 6x6 裁剪拼图。"""
import json, math, re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
import cv2, numpy as np
from clashlab.geo import Calib
ann = json.load(open(BASE + "/out/annotate/01_annotated.json", encoding="utf-8"))
img = cv2.imdecode(np.fromfile(BASE + "/android/assets/img/b01.jpg", np.uint8), cv2.IMREAD_COLOR)
m = re.search(r"quad=\[\[([^\]]+)\],\[([^\]]+)\],\[([^\]]+)\],\[([^\]]+)\]\]", ann["note"])
q = np.array([[float(v) for v in g.split(",")] for g in m.groups()], np.float32) * (img.shape[1] / 2622.0)
cal = Calib.from_quad(q, n=44)
th = next(b for b in ann["buildings"] if b["type"] == "town-hall")
thx, thy = th["tile"]
print("TH tile", thx, thy)
S = 160
canvas = np.full((S + 30, (S + 10) * 4, 3), 30, np.uint8)
for i, off in enumerate((0.5, 0.75, 1.0, 1.25)):
    cx, cy = thx + off, thy + off
    side = 6
    p = [cal.tile_to_px(cx - side/2, cy - side/2), cal.tile_to_px(cx + side/2, cy - side/2),
         cal.tile_to_px(cx + side/2, cy + side/2), cal.tile_to_px(cx - side/2, cy + side/2)]
    H = cv2.getPerspectiveTransform(np.float32(p), np.float32([[0,0],[S,0],[S,S],[0,S]]))
    crop = cv2.warpPerspective(img, H, (S, S), flags=cv2.INTER_AREA)
    x0 = 10 + i * (S + 10)
    canvas[30:30+S, x0:x0+S] = crop
    cv2.putText(canvas, "off+%.2f" % off, (x0, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 220, 255), 2)
cv2.imencode(".png", canvas)[1].tofile(BASE + "/out/layouts_src/th_offset_compare.png")
print("saved th_offset_compare.png")
