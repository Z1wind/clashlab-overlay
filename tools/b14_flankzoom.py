# -*- coding: utf-8 -*-
# b14_flankzoom.py — 左右翼深红蓝顶塔 / 顶条左块 6x 特写复核（新文件，中性命名）
import os, cv2, numpy as np
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
EN = os.path.join(ROOT, "out", "overlay", "enemy")
SCRATCH = r"C:\Users\Admin（无密码）\AppData\Local\Doubao\User Data\Default\.doubao\agent_mode\workspace\.sessions\38455881728595202\agents\s_0007xvhw26c\scratch"
buf = np.fromfile(os.path.join(EN, "b14_ov1.png"), dtype=np.uint8)
im = cv2.imdecode(buf, cv2.IMREAD_COLOR)
BOXES = {
    "flank_L": (300, 300, 400, 380),
    "flank_R": (900, 300, 990, 380),
    "north_patch": (320, 95, 520, 210),
    "west_edge": (250, 330, 360, 430),
    "east_edge": (950, 330, 1040, 430),
}
for name, (x0, y0, x1, y1) in BOXES.items():
    c = im[y0:y1, x0:x1]
    big = cv2.resize(c, None, fx=6.0, fy=6.0, interpolation=cv2.INTER_CUBIC)
    cv2.imencode(".png", big)[1].tofile(os.path.join(SCRATCH, f"z_{name}.png"))
    print(name, big.shape)
