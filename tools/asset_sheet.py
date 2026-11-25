# -*- coding: utf-8 -*-
# asset_sheet.py — 15 块联系表（带文件名标签）
import os, cv2, numpy as np
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
D = os.path.join(ROOT, "out", "overlay", "blocks")
tiles = [f"b{i:02d}.png" for i in range(15)]
thumbs = []
for f in tiles:
    im = cv2.imdecode(np.fromfile(os.path.join(D, f), dtype=np.uint8), cv2.IMREAD_COLOR)
    im = cv2.resize(im, (316, 183))
    cv2.putText(im, f, (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    thumbs.append(im)
rows = []
for r in range(5):
    rows.append(np.hstack(thumbs[r*3:(r+1)*3]))
sheet = np.vstack(rows)
ok, buf = cv2.imencode(".png", sheet)
out = os.path.join(ROOT, "tools", "base_out", "asset_sheet.png")
buf.tofile(out)
print("saved", out, sheet.shape)
