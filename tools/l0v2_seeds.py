# -*- coding: utf-8 -*-
# l0v2_seeds.py — 候选种子放大裁片（纯离线）；manifest: name:[cx,cy,half]
import os, cv2, numpy as np
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OV = os.path.join(ROOT, "out", "overlay")
OUT = os.path.join(ROOT, "tools", "base_out", "v2")
B = cv2.imdecode(np.fromfile(os.path.join(OV, "v6_l0_three_shot_base.png"), dtype=np.uint8), cv2.IMREAD_COLOR)
A = cv2.imdecode(np.fromfile(os.path.join(OV, "v6_l0_two_shot_base.png"), dtype=np.uint8), cv2.IMREAD_COLOR)
MAN = {
    "s1_tc_hall":   (481, 714, 46),
    "s2_wiz":       (451, 300, 42),
    "s3_archer":    (421, 185, 38),
    "s4_goldstor":  (120, 640, 44),
    "s5_darkstor":  (190, 555, 40),
    "s6_mortar":    (70, 720, 38),
    "s7_inferno":   (431, 260, 40),
    "s8_bombtower": (381, 250, 40),
    "s9_elixer":    (560, 660, 40),
    "s10_airsweep": (361, 120, 40),
}
for name, (cx, cy, h) in MAN.items():
    for tag, im in [("B", B), ("A", A)]:
        x0, y0 = max(0, cx - h), max(0, cy - h)
        crop = im[y0:min(im.shape[0], cy + h), x0:min(im.shape[1], cx + h)]
        big = cv2.resize(crop, (crop.shape[1] * 3, crop.shape[0] * 3), interpolation=cv2.INTER_CUBIC)
        cv2.imencode(".png", big)[1].tofile(os.path.join(OUT, f"seed_{name}_{tag}.png"))
print("done")
