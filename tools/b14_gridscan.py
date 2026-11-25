# -*- coding: utf-8 -*-
# b14_gridscan.py — 基地内部 3x2 重叠网格 3x 巡片，肉眼找防空碟（新文件）
import os, cv2, numpy as np
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
EN = os.path.join(ROOT, "out", "overlay", "enemy")
SCRATCH = r"C:\Users\Admin（无密码）\AppData\Local\Doubao\User Data\Default\.doubao\agent_mode\workspace\.sessions\38455881728595202\agents\s_0007xvhw26c\scratch"
buf = np.fromfile(os.path.join(EN, "b14_ov1.png"), dtype=np.uint8)
im = cv2.imdecode(buf, cv2.IMREAD_COLOR)
# 基地内部范围（含边缘角）
x0, y0, x1, y1 = 260, 80, 1010, 590
rows, cols = 2, 3
rw, cw = (x1 - x0) // cols + 60, (y1 - y0) // rows + 60
for r in range(rows):
    for c in range(cols):
        a = x0 + c * ((x1 - x0) // cols) - 30
        b = y0 + r * ((y1 - y0) // rows) - 30
        cc = min(x1, a + cw); d = min(y1, b + rw)
        tile = im[max(0, b):d, max(0, a):cc]
        big = cv2.resize(tile, None, fx=3.0, fy=3.0, interpolation=cv2.INTER_CUBIC)
        out = os.path.join(SCRATCH, f"b14_grid_r{r}c{c}.png")
        cv2.imencode(".png", big)[1].tofile(out)
        print(f"r{r}c{c}", (max(0, a), max(0, b), cc, d), big.shape)
