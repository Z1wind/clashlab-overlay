# -*- coding: utf-8 -*-
# b14_truth_tiles.py — 14_kekejdj 表面裁切 + 4x3 放大块（人工点数用，纯离线）
import os, cv2, numpy as np
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(ROOT, "tools", "base_out", "b14")
im = cv2.imdecode(np.fromfile(os.path.join(ROOT, "bases", "th16", "war_20261123", "14_kekejdj.png"), dtype=np.uint8), cv2.IMREAD_COLOR)
# surface L15 T35 R1024 B585
sur = im[35:585, 15:1024]
h, w = sur.shape[:2]
cols, rows = 4, 3
cw, ch = w // cols, h // rows
for r in range(rows):
    for c in range(cols):
        x0, y0 = c * cw, r * ch
        crop = sur[y0:y0 + ch, x0:x0 + cw].copy()
        for x in range(0, cw, 50):
            cv2.line(crop, (x, 0), (x, ch), (0, 255, 255), 1)
            cv2.putText(crop, str(x0 + x), (x + 2, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
        for y in range(0, ch, 50):
            cv2.line(crop, (0, y), (cw, y), (0, 255, 255), 1)
            cv2.putText(crop, str(y0 + y), (2, y + 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
        big = cv2.resize(crop, (cw * 2, ch * 2), interpolation=cv2.INTER_CUBIC)
        cv2.imencode(".png", big)[1].tofile(os.path.join(OUT, f"t14_r{r}c{c}.png"))
print("surface", sur.shape)
