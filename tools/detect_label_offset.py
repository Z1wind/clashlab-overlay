# -*- coding: utf-8 -*-
"""检测每张标注是否存在全局 tile 偏移（用裁剪纹理能量最大化搜索）。"""
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab.geo import Calib
DL = os.path.join(os.path.expanduser("~"), "Downloads")
for i in range(1, 9):
    d = json.load(open(os.path.join(DL, "annot_b%02d.json" % i), encoding="utf-8"))
    img = cv2.imdecode(np.fromfile(os.path.join(BASE, "android", "assets", "img", "b%02d.jpg" % i), np.uint8), cv2.IMREAD_COLOR)
    wn, hn = d["image_size"]; quad = np.float32([[u*wn, v*hn] for u, v in d["corners_norm"]])
    cal = Calib.from_quad(quad, n=44)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY); lap = cv2.Laplacian(gray, cv2.CV_32F)
    energy = cv2.blur(lap*lap, (9,9))
    def score(dx, dy):
        vals = []
        for b in d["buildings"]:
            x, y = b["tile"]
            p = cal.tile_to_px(x + .5 + dx, y + .5 + dy)
            xi, yi = int(p[0]), int(p[1])
            if 0 <= xi < img.shape[1] and 0 <= yi < img.shape[0]:
                vals.append(energy[yi, xi])
        return float(np.mean(vals)) if vals else -1
    best = max(((score(dx, dy), dx, dy) for dx in range(-3,4) for dy in range(-3,4)), key=lambda t: t[0])
    base0 = score(0, 0)
    print("b%02d" % i, "score0=%.1f" % base0, "best=%.1f offset=(%d,%d)" % best)
