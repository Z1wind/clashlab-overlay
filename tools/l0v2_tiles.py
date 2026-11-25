# -*- coding: utf-8 -*-
# l0v2_tiles.py — A/B 帧分块放大，供人工盘点（纯离线）
import os, cv2, numpy as np
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OV = os.path.join(ROOT, "out", "overlay")
OUT = os.path.join(ROOT, "tools", "base_out", "v2")
os.makedirs(OUT, exist_ok=True)
for tag, fn in [("A", "v6_l0_two_shot_base.png"), ("B", "v6_l0_three_shot_base.png")]:
    im = cv2.imdecode(np.fromfile(os.path.join(OV, fn), dtype=np.uint8), cv2.IMREAD_COLOR)
    h, w = im.shape[:2]
    cols, rows = 3, 2
    cw, ch = w // cols, h // rows
    for r in range(rows):
        for c in range(cols):
            crop = im[r * ch:(r + 1) * ch, c * cw:(c + 1) * cw]
            big = cv2.resize(crop, (cw * 2, ch * 2), interpolation=cv2.INTER_CUBIC)
            cv2.imencode(".png", big)[1].tofile(os.path.join(OUT, f"{tag}_r{r}c{c}.png"))
print("done")
