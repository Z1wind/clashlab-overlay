# -*- coding: utf-8 -*-
"""生成六阵 2D 俯视图 + 2D 交换 JSON。"""
import json, os, sys
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab.topdown import render_topdown, export_2d_json
OUT = os.path.join(BASE, "out", "overlay", "_2d")
os.makedirs(OUT, exist_ok=True)
for name in ("01", "02", "03", "04", "05", "06"):
    lay = json.load(open(os.path.join(BASE, "bases", "th16", name, "layout.json"), encoding="utf-8"))
    png = os.path.join(OUT, "%s_topdown.png" % name)
    w, h, nb, nw = render_topdown(lay, png, cell=24)
    export_2d_json(lay, os.path.join(OUT, "%s_2d.json" % name))
    print(name, "png", w, "x", h, "buildings", nb, "walls", nw, "bytes", os.path.getsize(png))
