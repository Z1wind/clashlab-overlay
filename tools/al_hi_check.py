# -*- coding: utf-8 -*-
"""检查高倍标签裁剪是否居中：把 18 个 300×300 裁剪拼成接触表。"""
import json, os
import numpy as np, cv2
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
HI = os.path.join(BASE, "out", "overlay", "_auto_label", "hi")
labels = json.load(open(os.path.join(HI, "labels_hi.json"), encoding="utf-8"))
imgs = {}
cell = 150
cols = 6
sheet = np.full((3 * (cell + 18), cols * cell, 3), 40, np.uint8)
for i, r in enumerate(labels):
    v = r["view"]
    if v not in imgs:
        imgs[v] = cv2.imdecode(np.fromfile(os.path.join(HI, v + ".png"), np.uint8), cv2.IMREAD_COLOR)
    img = imgs[v]
    half = 150
    x0 = min(max(0, r["x"] - half), img.shape[1] - 300)
    y0 = min(max(0, r["y"] - half), img.shape[0] - 300)
    c = cv2.resize(img[y0:y0 + 300, x0:x0 + 300], (cell, cell), interpolation=cv2.INTER_AREA)
    rr, cc = divmod(i, cols)
    sheet[rr * (cell + 18):rr * (cell + 18) + cell, cc * cell:(cc + 1) * cell] = c
    cv2.putText(sheet, r["type"][:14], (cc * cell + 2, rr * (cell + 18) + cell + 13),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
cv2.imencode(".png", sheet)[1].tofile(os.path.join(HI, "check_sheet.png"))
print("wrote check_sheet.png")
