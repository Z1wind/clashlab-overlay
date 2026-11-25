# -*- coding: utf-8 -*-
# b14_centerzoom.py — 核心区 4x 特写，定位 TH/monolith/CC/法术塔（新文件）
import os, cv2, numpy as np
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
EN = os.path.join(ROOT, "out", "overlay", "enemy")
SCRATCH = r"C:\Users\Admin（无密码）\AppData\Local\Doubao\User Data\Default\.doubao\agent_mode\workspace\.sessions\38455881728595202\agents\s_0007xvhw26c\scratch"
buf = np.fromfile(os.path.join(EN, "b14_ov1.png"), dtype=np.uint8)
im = cv2.imdecode(buf, cv2.IMREAD_COLOR)
BOXES = {
    "core": (540, 290, 780, 480),
    "west_ring": (280, 200, 480, 420),
    "south_ring": (480, 460, 720, 600),
}
for name, (x0, y0, x1, y1) in BOXES.items():
    c = im[y0:y1, x0:x1]
    big = cv2.resize(c, None, fx=4.0, fy=4.0, interpolation=cv2.INTER_CUBIC)
    cv2.imencode(".png", big)[1].tofile(os.path.join(SCRATCH, f"c_{name}.png"))
    print(name, big.shape)
