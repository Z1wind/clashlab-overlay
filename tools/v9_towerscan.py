# -*- coding: utf-8 -*-
# v9 复核：全图候选塔位 3x 特写，逐个判类型（找防空火箭=蓝碟）
import cv2, numpy as np, os
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
SCRATCH = r"C:\Users\Admin（无密码）\AppData\Local\Doubao\User Data\Default\.doubao\agent_mode\workspace\.sessions\38455881728595202\agents\s_0007xvhw26c\scratch"
buf = np.fromfile(os.path.join(ROOT, "out", "overlay", "v6_l0_three_shot_base.png"), dtype=np.uint8)
im = cv2.imdecode(buf, cv2.IMREAD_COLOR)
z = 3.0
# (名称, cx, cy, half)
BOXES = {
    "t_north": (455, 175, 55),
    "t_west": (300, 385, 55),
    "t_ne": (715, 250, 55),
    "t_south": (415, 730, 55),
    "t_se": (655, 660, 55),
    "cube_ne": (575, 360, 50),
    "orange_s": (455, 640, 55),
    "blue_c": (560, 560, 50),
    "machine_w": (255, 470, 70),
    "dark_mid": (385, 470, 55),
    "cc_mid": (500, 470, 50),
    "dark_e": (640, 470, 45),
    "th_e": (700, 450, 70),
}
for name, (cx, cy, hh) in BOXES.items():
    x0, y0 = max(0, cx - hh), max(0, cy - hh)
    x1, y1 = min(im.shape[1], cx + hh), min(im.shape[0], cy + hh)
    c = im[y0:y1, x0:x1]
    big = cv2.resize(c, None, fx=z, fy=z, interpolation=cv2.INTER_CUBIC)
    out = os.path.join(SCRATCH, f"tw_{name}.png")
    cv2.imencode(".png", big)[1].tofile(out)
    print(name, (x0, y0, x1, y1))
