# -*- coding: utf-8 -*-
"""从 clashofclans-layouts 原始图纸 + 标注 tile 生成真实域裁剪样本（正=建筑带类型，负=背景/墙）。"""
import glob, json, os, random, re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab.geo import Calib
from clashlab.assets import STATS
S = 96
MAP = {
    "01_annotated.json": "war_138.jpg",
    "03_annotated.json": "war_143.jpg",
    "04_annotated.json": "war_141.jpg",
    "05_annotated.json": "war_139.jpg",
    "06_annotated.json": "defence_17.jpg",
}
random.seed(7); np.random.seed(7)

def parse_quad(note):
    m = re.search(r"quad=\[\[([^\]]+)\],\[([^\]]+)\],\[([^\]]+)\],\[([^\]]+)\]\]", note or "")
    if not m:
        return None
    return np.array([[float(x) for x in g.split(",")] for g in m.groups()], np.float32)

def crop_window(img, cal, x, y, size):
    p = [cal.tile_to_px(x, y), cal.tile_to_px(x + size, y), cal.tile_to_px(x + size, y + size), cal.tile_to_px(x, y + size)]
    H = cv2.getPerspectiveTransform(np.float32(p), np.float32([[0, 0], [S, 0], [S, S], [0, S]]))
    return cv2.warpPerspective(img, H, (S, S), flags=cv2.INTER_AREA)

imgs, labels = [], []
for ann_name, src_name in MAP.items():
    ann = json.load(open(os.path.join(BASE, "out", "annotate", ann_name), encoding="utf-8"))
    src = os.path.join(BASE, "out", "layouts_src", src_name)
    img = cv2.imdecode(np.fromfile(src, np.uint8), cv2.IMREAD_COLOR)
    quad = parse_quad(ann.get("note"))
    if img is None or quad is None:
        print("skip", ann_name); continue
    cal = Calib.from_quad(quad, 44)
    occ = set()
    pos = 0
    for b in ann.get("buildings") or []:
        t = b.get("type"); tile = b.get("tile") or [0, 0]
        size = int((STATS.get(t) or {}).get("size") or 2)
        x, y = int(round(tile[0])), int(round(tile[1]))
        for dx in range(size):
            for dy in range(size):
                occ.add((x + dx, y + dy))
        if x < 0 or y < 0 or x + size > 44 or y + size > 44:
            continue
        crop = crop_window(img, cal, x, y, size)
        imgs.append(crop); labels.append({"type": t, "image": src_name, "tile": [x, y], "size": size}); pos += 1
    neg = 0
    tries = 0
    while neg < 400 and tries < 8000:
        tries += 1
        size = random.choice((2, 2, 3, 4))
        x = random.randint(0, 44 - size); y = random.randint(0, 44 - size)
        near = any((x + dx, y + dy) in occ for dx in range(size) for dy in range(size))
        if near:
            continue
        crop = crop_window(img, cal, x, y, size)
        g = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        if cv2.Laplacian(g, cv2.CV_64F).var() < 20:
            continue
        imgs.append(crop); labels.append({"type": "__bg__", "image": src_name, "tile": [x, y], "size": size}); neg += 1
    print(ann_name, "->", src_name, "pos", pos, "neg", neg)
arr = np.stack(imgs, 0)
out = os.path.join(BASE, "datasets", "real_layout")
os.makedirs(out, exist_ok=True)
np.save(os.path.join(out, "imgs.npy"), arr)
json.dump(labels, open(os.path.join(out, "labels.json"), "w", encoding="utf-8"), ensure_ascii=False)
print("saved", arr.shape, "labels", len(labels))
print("types:", len({l["type"] for l in labels}))
