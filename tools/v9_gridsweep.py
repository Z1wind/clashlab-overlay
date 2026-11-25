# -*- coding: utf-8 -*-
# v9 复核：全基 3x2 网格 2x 巡片，找蓝色防空碟
import cv2, numpy as np, os
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
SCRATCH = r"C:\Users\Admin（无密码）\AppData\Local\Doubao\User Data\Default\.doubao\agent_mode\workspace\.sessions\38455881728595202\agents\s_0007xvhw26c\scratch"
buf = np.fromfile(os.path.join(ROOT, "out", "overlay", "v6_l0_three_shot_base.png"), dtype=np.uint8)
im = cv2.imdecode(buf, cv2.IMREAD_COLOR)
H, W = im.shape[:2]
z = 2.0
rows, cols = 2, 3
for r in range(rows):
    for c in range(cols):
        x0 = int(c * W / cols); x1 = int((c + 1) * W / cols)
        y0 = int(r * H / rows); y1 = int((r + 1) * H / rows)
        seg = im[y0:y1, x0:x1]
        big = cv2.resize(seg, None, fx=z, fy=z, interpolation=cv2.INTER_CUBIC)
        out = os.path.join(SCRATCH, f"grid_r{r}c{c}.png")
        cv2.imencode(".png", big)[1].tofile(out)
        print(f"r{r}c{c}", (x0, y0, x1, y1))
