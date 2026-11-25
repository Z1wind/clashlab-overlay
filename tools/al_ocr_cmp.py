# -*- coding: utf-8 -*-
"""OCR 参数对比：目标文本「兵营（12级）」在 (560..790, 465..500)。"""
import json, sys
import numpy as np, cv2
from PIL import Image
import winocr

src = sys.argv[1]
out = sys.argv[2]
img = cv2.imdecode(np.fromfile(src, np.uint8), cv2.IMREAD_COLOR)


def run(name, region, scale, mode="plain"):
    x0, y0, x1, y1 = region
    reg = img[y0:y1, x0:x1]
    g = cv2.cvtColor(reg, cv2.COLOR_BGR2GRAY)
    if mode == "clahe":
        g = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(g)
    elif mode == "thresh":
        g = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(g)
        _, g = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    elif mode == "invert":
        g = 255 - g
    g = cv2.resize(g, (int(g.shape[1] * scale), int(g.shape[0] * scale)), interpolation=cv2.INTER_LANCZOS4)
    pil = Image.fromarray(g).convert("RGB")
    r = winocr.recognize_pil_sync(pil, "zh-Hans")
    return {"name": name, "text": r.get("text", ""), "lines": [l.get("text", "") for l in r.get("lines", [])]}


tests = [
    ("card_x3", (430, 440, 860, 522), 3, "plain"),
    ("card_x2_clahe", (430, 440, 860, 522), 2, "clahe"),
    ("card_x4_clahe", (430, 440, 860, 522), 4, "clahe"),
    ("name_x4", (540, 460, 800, 505), 4, "plain"),
    ("name_x4_clahe", (540, 460, 800, 505), 4, "clahe"),
    ("name_x6_clahe", (540, 460, 800, 505), 6, "clahe"),
    ("name_x4_thresh", (540, 460, 800, 505), 4, "thresh"),
    ("full_x2", (0, 0, 1280, 720), 2, "plain"),
]
res = [run(*t) for t in tests]
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for r in res:
    print(r["name"], "->", len(r["text"]))
