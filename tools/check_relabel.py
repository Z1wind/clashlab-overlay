# -*- coding: utf-8 -*-
"""校验重标的 b01/b02（annot_b01 (1).json / annot_b02 (1).json）。"""
import json, os, shutil, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab.geo import Calib
DL = os.path.join(os.path.expanduser("~"), "Downloads")
OUT = os.path.join(BASE, "out", "apk_qa", "relabel")
os.makedirs(OUT, exist_ok=True)
for src, dst in (("annot_b01 (1).json", "b01.json"), ("annot_b02 (1).json", "b02.json")):
    p = os.path.join(DL, src)
    if not os.path.exists(p):
        print("MISSING", p); continue
    shutil.copyfile(p, os.path.join(OUT, dst))
    d = json.load(open(p, encoding="utf-8"))
    b = d.get("buildings") or []
    cn = d.get("corners_norm") or []
    img_i = 1 if "01" in dst else 2
    img = cv2.imdecode(np.fromfile(os.path.join(BASE, "android", "assets", "img", "b%02d.jpg" % img_i), np.uint8), cv2.IMREAD_COLOR)
    wn, hn = d["image_size"]; quad = np.float32([[u*wn, v*hn] for u, v in cn])
    cal = Calib.from_quad(quad, n=44)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY); lap = cv2.Laplacian(gray, cv2.CV_32F)
    energy = cv2.blur(lap*lap, (9,9))
    vals = []
    for x in b:
        px, py = cal.tile_to_px(x["tile"][0] + .5, x["tile"][1] + .5)
        xi, yi = int(px), int(py)
        if 0 <= xi < img.shape[1] and 0 <= yi < img.shape[0]: vals.append(energy[yi, xi])
    print(dst, "| ver", d.get("version"), "| size", d.get("image_size"), "| corners", len(cn),
          "| bld", len(b), "| types", len(set(x.get("type") for x in b)),
          "| tile x", (min(x["tile"][0] for x in b), max(x["tile"][0] for x in b)),
          "| tile y", (min(x["tile"][1] for x in b), max(x["tile"][1] for x in b)),
          "| meanEnergy", round(float(np.mean(vals)), 1) if vals else None)
