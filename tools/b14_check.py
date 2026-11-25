# -*- coding: utf-8 -*-
# b14_check.py — 裁图自检：左上轴图区 + 走点标签区（新文件）
import os, cv2, numpy as np
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
SCRATCH = r"C:\Users\Admin（无密码）\AppData\Local\Doubao\User Data\Default\.doubao\agent_mode\workspace\.sessions\38455881728595202\agents\s_0007xvhw26c\scratch"
buf = np.fromfile(os.path.join(ROOT, "out", "overlay", "v9b_queen_giantarrow_b14.png"), dtype=np.uint8)
im = cv2.imdecode(buf, cv2.IMREAD_COLOR)
crops = {
    "chk_topleft": (0, 150, 760, 560),
    "chk_path": (400, 480, 1100, 760),
}
for name, (x0, y0, x1, y1) in crops.items():
    c = im[y0:y1, x0:x1]
    cv2.imencode(".png", c)[1].tofile(os.path.join(SCRATCH, f"{name}.png"))
    print(name, c.shape)
