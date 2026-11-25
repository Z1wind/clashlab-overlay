# -*- coding: utf-8 -*-
# b14_topzoom.py — 顶条/四边中点 5x 特写，复核疑似防空碟（新文件）
import os, cv2, numpy as np
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
EN = os.path.join(ROOT, "out", "overlay", "enemy")
SCRATCH = r"C:\Users\Admin（无密码）\AppData\Local\Doubao\User Data\Default\.doubao\agent_mode\workspace\.sessions\38455881728595202\agents\s_0007xvhw26c\scratch"
buf = np.fromfile(os.path.join(EN, "b14_ov1.png"), dtype=np.uint8)
im = cv2.imdecode(buf, cv2.IMREAD_COLOR)
BOXES = {
    "top_center": (500, 80, 790, 230),
    "left_mid": (280, 280, 430, 400),
    "right_mid": (880, 290, 1010, 410),
    "bottom_mid": (500, 500, 700, 610),
    "top_left": (300, 90, 520, 220),
    "top_right": (760, 90, 1000, 230),
}
for name, (x0, y0, x1, y1) in BOXES.items():
    c = im[y0:y1, x0:x1]
    big = cv2.resize(c, None, fx=5.0, fy=5.0, interpolation=cv2.INTER_CUBIC)
    cv2.imencode(".png", big)[1].tofile(os.path.join(SCRATCH, f"b14_zoom_{name}.png"))
    print(name, big.shape)
