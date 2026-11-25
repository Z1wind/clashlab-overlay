# -*- coding: utf-8 -*-
# b14_candmontage.py — 蓝簇候选4x特写拼图，逐个判类型（新文件）
import os, cv2, numpy as np
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
EN = os.path.join(ROOT, "out", "overlay", "enemy")
SCRATCH = r"C:\Users\Admin（无密码）\AppData\Local\Doubao\User Data\Default\.doubao\agent_mode\workspace\.sessions\38455881728595202\agents\s_0007xvhw26c\scratch"
buf = np.fromfile(os.path.join(EN, "b14_ov1.png"), dtype=np.uint8)
im = cv2.imdecode(buf, cv2.IMREAD_COLOR)

CANDS = {
    0: (756, 148), 2: (700, 338), 4: (831, 411), 5: (358, 340),
    6: (578, 175), 7: (925, 340), 8: (452, 411), 9: (704, 175),
    10: (694, 498), 11: (589, 498), 15: (646, 156), 18: (515, 179),
}
z = 4.0; half = 42
tiles = []
for k, (cx, cy) in CANDS.items():
    x0, y0 = max(0, cx - half), max(0, cy - half)
    c = im[y0:cy + half, x0:cx + half]
    big = cv2.resize(c, None, fx=z, fy=z, interpolation=cv2.INTER_CUBIC)
    cv2.putText(big, f"#{k} ({cx},{cy})", (6, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    tiles.append(big)
cols = 4
rows = (len(tiles) + cols - 1) // cols
th, tw = tiles[0].shape[:2]
sheet = np.full((rows * th, cols * tw, 3), 240, np.uint8)
for i, t in enumerate(tiles):
    r, c = divmod(i, cols)
    sheet[r * th:(r + 1) * th, c * tw:(c + 1) * tw] = t
cv2.imencode(".png", sheet)[1].tofile(os.path.join(SCRATCH, "b14_candmontage.png"))
print("sheet", sheet.shape)
