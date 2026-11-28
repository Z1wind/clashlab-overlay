# -*- coding: utf-8 -*-
"""检测标注坐标是否镜像/转置：对 8 种变换各算纹理能量。"""
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab.geo import Calib
DL = os.path.join(os.path.expanduser("~"), "Downloads")
TR = {
 "id":      lambda x,y:(x,y),
 "swap":    lambda x,y:(y,x),
 "mx":      lambda x,y:(44-x,y),
 "my":      lambda x,y:(x,44-y),
 "mxy":     lambda x,y:(44-x,44-y),
 "swap_mx": lambda x,y:(y,44-x),
 "swap_my": lambda x,y:(44-y,x),
 "swap_mxy":lambda x,y:(44-y,44-x),
}
for i in (1,2,3,6):
    d = json.load(open(os.path.join(DL, "annot_b%02d.json" % i), encoding="utf-8"))
    img = cv2.imdecode(np.fromfile(os.path.join(BASE, "android", "assets", "img", "b%02d.jpg" % i), np.uint8), cv2.IMREAD_COLOR)
    wn, hn = d["image_size"]; quad = np.float32([[u*wn, v*hn] for u, v in d["corners_norm"]])
    cal = Calib.from_quad(quad, n=44)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY); lap = cv2.Laplacian(gray, cv2.CV_32F)
    energy = cv2.blur(lap*lap, (9,9))
    H_, W_ = img.shape[:2]
    scores = {}
    for name, fn in TR.items():
        vals = []
        for b in d["buildings"]:
            x, y = b["tile"]; tx, ty = fn(x, y)
            p = cal.tile_to_px(tx + .5, ty + .5)
            xi, yi = int(p[0]), int(p[1])
            if 0 <= xi < W_ and 0 <= yi < H_:
                vals.append(energy[yi, xi])
        scores[name] = float(np.mean(vals)) if vals else -1
    best = max(scores, key=scores.get)
    print("b%02d" % i, "best=%s" % best, {k: round(v) for k, v in scores.items()})
