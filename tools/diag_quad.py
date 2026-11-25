# -*- coding: utf-8 -*-
"""诊断：用 layout.json note 里的 quad 画网格到 base.png，看贴合度。"""
import json, os, re
import numpy as np, cv2
import sys
sys.path.insert(0, r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat")
from clashlab.geo import Calib
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(BASE, "out", "import")
os.makedirs(OUT, exist_ok=True)
quad_re = re.compile(r"quad\s*=\s*\[\[[^\]]+\](?:\s*,\s*\[[^\]]+\]){3,}\]")
for n in ("01", "03", "05"):
    lay = json.load(open(os.path.join(BASE, "bases", "th16", n, "layout.json"), encoding="utf-8"))
    m = quad_re.search(lay.get("note") or "")
    if not m:
        print(n, "no quad"); continue
    quad = json.loads(m.group(0).split("=", 1)[1])
    img = cv2.imdecode(np.fromfile(os.path.join(BASE, "bases", "th16", n, "base.png"), np.uint8), cv2.IMREAD_COLOR)
    calib = Calib.from_quad(quad, n=44)
    vis = img.copy()
    for i in range(45):
        p0 = calib.tile_to_px(i, 0); p1 = calib.tile_to_px(i, 44)
        q0 = calib.tile_to_px(0, i); q1 = calib.tile_to_px(44, i)
        cv2.line(vis, tuple(np.int32(p0)), tuple(np.int32(p1)), (0, 255, 0), 2)
        cv2.line(vis, tuple(np.int32(q0)), tuple(np.int32(q1)), (255, 128, 0), 2)
    p = os.path.join(OUT, n + "_quadcheck.png")
    cv2.imencode(".png", vis)[1].tofile(p)
    print(n, "quad=", quad, "->", p, os.path.getsize(p), "B")
