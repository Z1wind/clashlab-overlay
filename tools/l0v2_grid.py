# -*- coding: utf-8 -*-
# l0v2_grid.py — B 帧叠加 50px 坐标网格，分四张象限大图供定点（纯离线）
import os, cv2, numpy as np
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OV = os.path.join(ROOT, "out", "overlay")
OUT = os.path.join(ROOT, "tools", "base_out", "v2")
B = cv2.imdecode(np.fromfile(os.path.join(OV, "v6_l0_three_shot_base.png"), dtype=np.uint8), cv2.IMREAD_COLOR)
h, w = B.shape[:2]
g = B.copy()
for x in range(0, w, 50):
    cv2.line(g, (x, 0), (x, h), (0, 255, 255), 1)
    cv2.putText(g, str(x), (x + 2, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 255), 1)
for y in range(0, h, 50):
    cv2.line(g, (0, y), (w, y), (0, 255, 255), 1)
    cv2.putText(g, str(y), (2, y + 12), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 255), 1)
# 四象限 2x
quads = [(0, 0, 480, 560), (440, 0, 905, 560), (0, 520, 480, 1068), (440, 520, 905, 1068)]
for i, (x0, y0, x1, y1) in enumerate(quads):
    crop = g[y0:y1, x0:x1]
    big = cv2.resize(crop, ((x1 - x0) * 2, (y1 - y0) * 2), interpolation=cv2.INTER_CUBIC)
    cv2.imencode(".png", big)[1].tofile(os.path.join(OUT, f"grid_q{i}.png"))
print("done")
