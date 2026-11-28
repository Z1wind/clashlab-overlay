# -*- coding: utf-8 -*-
"""把用户的标注画到图上，检查 b01/b02 是否偏移。"""
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab.geo import Calib
DL = os.path.join(os.path.expanduser("~"), "Downloads")
for i in (1, 2, 6):
    d = json.load(open(os.path.join(DL, "annot_b%02d.json" % i), encoding="utf-8"))
    img = cv2.imdecode(np.fromfile(os.path.join(BASE, "android", "assets", "img", "b%02d.jpg" % i), np.uint8), cv2.IMREAD_COLOR)
    H, W = img.shape[:2]
    wn, hn = d["image_size"]
    quad = np.float32([[u * wn, v * hn] for u, v in d["corners_norm"]])
    cal = Calib.from_quad(quad, n=44)
    vis = img.copy()
    for b in d["buildings"]:
        x, y = b["tile"]; p = cal.tile_to_px(x + .5, y + .5)
        cv2.circle(vis, (int(p[0]), int(p[1])), 6, (0, 0, 255), 2)
    for k in range(0, 45, 4):
        a = cal.tile_to_px(k, 0); bb = cal.tile_to_px(k, 44); c = cal.tile_to_px(0, k); dd = cal.tile_to_px(44, k)
        cv2.line(vis, (int(a[0]), int(a[1])), (int(bb[0]), int(bb[1])), (0, 255, 255), 1)
        cv2.line(vis, (int(c[0]), int(c[1])), (int(dd[0]), int(dd[1])), (0, 255, 255), 1)
    out = os.path.join(BASE, "out", "apk_qa", "user_labels_b%02d.png" % i)
    cv2.imencode(".png", vis)[1].tofile(out)
    print("saved", out, "| corners", np.round(d["corners_norm"], 3).tolist())
