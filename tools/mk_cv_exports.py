# -*- coding: utf-8 -*-
"""把 5 张已有标注转成 v2 导出（b01..b05），用于多基 CV 烟测。"""
import json, os, re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
PAIRS = [("01_annotated.json","b01.jpg"),("03_annotated.json","b02.jpg"),("04_annotated.json","b03.jpg"),
         ("05_annotated.json","b04.jpg"),("06_annotated.json","b05.jpg")]
outdir = os.path.join(BASE, "out", "apk_qa", "cv_exports")
os.makedirs(outdir, exist_ok=True)
paths = []
for ann_name, img_name in PAIRS:
    ann = json.load(open(os.path.join(BASE, "out", "annotate", ann_name), encoding="utf-8"))
    img = cv2.imdecode(np.fromfile(os.path.join(BASE, "android", "assets", "img", img_name), np.uint8), cv2.IMREAD_COLOR) if False else None
    p = os.path.join(BASE, "android", "assets", "img", img_name)
    import numpy as np
    im = cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)
    H, W = im.shape[:2]
    m = re.search(r"quad=\[\[([^\]]+)\],\[([^\]]+)\],\[([^\]]+)\],\[([^\]]+)\]\]", ann.get("note") or "")
    q = [[float(v) for v in g.split(",")] for g in m.groups()]
    sc = W / 2622.0
    doc = {"version": 2, "image": "img/" + img_name, "image_size": [W, H], "grid": 44,
           "corners": [[x * sc, y * sc] for x, y in q],
           "corners_norm": [[x * sc / W, y * sc / H] for x, y in q],
           "buildings": [{"type": b["type"], "name": b.get("name") or b["type"], "tile": b["tile"]} for b in ann["buildings"]]}
    op = os.path.join(outdir, img_name.replace(".jpg", ".json"))
    json.dump(doc, open(op, "w", encoding="utf-8"), ensure_ascii=False)
    paths.append(op)
    print(img_name, "buildings", len(doc["buildings"]), "size", W, H)
print("EXPORTS=" + ",".join(paths))
