# -*- coding: utf-8 -*-
# b14_towerzoom.py — 侧翼红塔单体 8x 特写（新文件）
import os, cv2, numpy as np
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
EN = os.path.join(ROOT, "out", "overlay", "enemy")
SCRATCH = r"C:\Users\Admin（无密码）\AppData\Local\Doubao\User Data\Default\.doubao\agent_mode\workspace\.sessions\38455881728595202\agents\s_0007xvhw26c\scratch"
buf = np.fromfile(os.path.join(EN, "b14_ov1.png"), dtype=np.uint8)
im = cv2.imdecode(buf, cv2.IMREAD_COLOR)
BOXES = {
    "tw_L": (296, 312, 352, 372),
    "tw_R": (948, 312, 1004, 372),
    "east_tower": (955, 330, 1040, 430),
}
for name, (x0, y0, x1, y1) in BOXES.items():
    c = im[y0:y1, x0:x1]
    big = cv2.resize(c, None, fx=8.0, fy=8.0, interpolation=cv2.INTER_CUBIC)
    cv2.imencode(".png", big)[1].tofile(os.path.join(SCRATCH, f"t_{name}.png"))
    print(name, big.shape)
