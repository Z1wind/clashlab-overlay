# -*- coding: utf-8 -*-
# b14_tiles.py — b14_full 分块放大 + 坐标网格，供人工点数（纯离线）
import os, cv2, numpy as np
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(ROOT, "tools", "base_out", "b14")
os.makedirs(OUT, exist_ok=True)
im = cv2.imdecode(np.fromfile(os.path.join(ROOT, "out", "overlay", "enemy", "b14_full.png"), dtype=np.uint8), cv2.IMREAD_COLOR)
h, w = im.shape[:2]
print("shape", im.shape)
cols, rows = 3, 2
cw, ch = w // cols, h // rows
for r in range(rows):
    for c in range(cols):
        x0, y0 = c * cw, r * ch
        crop = im[y0:y0 + ch, x0:x0 + cw].copy()
        # 50px 网格（原坐标）
        for x in range(0, cw, 50):
            cv2.line(crop, (x, 0), (x, ch), (0, 255, 255), 1)
            cv2.putText(crop, str(x0 + x), (x + 2, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 255), 1)
        for y in range(0, ch, 50):
            cv2.line(crop, (0, y), (cw, y), (0, 255, 255), 1)
            cv2.putText(crop, str(y0 + y), (2, y + 12), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 255), 1)
        big = cv2.resize(crop, (cw * 3, ch * 3), interpolation=cv2.INTER_CUBIC)
        cv2.imencode(".png", big)[1].tofile(os.path.join(OUT, f"b14_r{r}c{c}.png"))
print("done")
