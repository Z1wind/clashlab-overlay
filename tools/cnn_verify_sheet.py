# -*- coding: utf-8 -*-
"""标注自查：把 67 条标注的裁剪拼成带标签的接触表，用于人工逐条复核。"""
import json, os, math
import numpy as np, cv2
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
HI = os.path.join(BASE, "out", "overlay", "_auto_label", "hi")
MAX = os.path.join(BASE, "out", "overlay", "_recon", "max")
rows = []
for fn in ("labels_max.json", "labels_max2.json", "labels_max3.json", "labels_max4.json"):
    p = os.path.join(HI, fn)
    if os.path.exists(p):
        rows += json.load(open(p, encoding="utf-8"))
imgs, cell, cols = {}, 104, 9
n = len(rows)
sheet = np.full((math.ceil(n / cols) * (cell + 16), cols * cell, 3), 30, np.uint8)
for i, r in enumerate(rows):
    b = r["block"]
    if b not in imgs:
        imgs[b] = cv2.imdecode(np.fromfile(os.path.join(MAX, b + ".png"), np.uint8), cv2.IMREAD_COLOR)
    img = imgs[b]
    half = 150
    x0 = max(0, min(r["x"] - half, img.shape[1] - 300))
    y0 = max(0, min(r["y"] - half, img.shape[0] - 300))
    c = cv2.resize(img[y0:y0 + 300, x0:x0 + 300], (cell, cell), interpolation=cv2.INTER_AREA)
    rr, cc = divmod(i, cols)
    sheet[rr * (cell + 16):rr * (cell + 16) + cell, cc * cell:(cc + 1) * cell] = c
    cv2.putText(sheet, "%d %s" % (i, r["type"][:11]), (cc * cell + 1, rr * (cell + 16) + cell + 12),
                cv2.FONT_HERSHEY_SIMPLEX, 0.34, (255, 255, 255), 1)
cv2.imencode(".png", sheet)[1].tofile(os.path.join(HI, "verify_sheet.png"))
json.dump(rows, open(os.path.join(HI, "verify_labels.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("rows=%d sheet=%s" % (n, sheet.shape))
