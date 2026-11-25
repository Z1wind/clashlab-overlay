# -*- coding: utf-8 -*-
"""把 17 个 high 候选的 box_px 区域从 overlay.png 裁出，拼联系表供人工指定类型。"""
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from clashlab.vision import imread, imwrite
import cv2, numpy as np

c = json.load(open(os.path.join(ROOT, "out/check_verify/home_village/layout_candidates.json"), encoding="utf-8"))
high = [x for x in c["candidates"] if x["tier"] == "high"]
ov = imread(os.path.join(ROOT, "out/check_verify/home_village/overlay.png"))
h, w = ov.shape[:2]
R = 70
cols, cell = 4, 160
rows = (len(high) + cols - 1) // cols
sheet = np.full((rows * cell, cols * cell, 3), 255, dtype=np.uint8)
for i, x in enumerate(high):
    bx, by, bw, bh = x["box_px"]
    cx, cy = bx + bw // 2, by + bh // 2
    x0, y0 = max(0, cx - R), max(0, cy - R)
    x1, y1 = min(w, cx + R), min(h, cy + R)
    crop = ov[y0:y1, x0:x1]
    crop = cv2.resize(crop, (cell - 10, cell - 35))
    r, cc = divmod(i, cols)
    y, xx = r * cell, cc * cell
    sheet[y + 25:y + cell - 10, xx + 5:xx + cell - 5] = crop
    cv2.putText(sheet, f"#{i} {x['type']}", (xx + 8, y + 18),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)
out = os.path.join(ROOT, "out/snap/annot/high_sheet.png")
imwrite(out, sheet)
print("saved", out)
