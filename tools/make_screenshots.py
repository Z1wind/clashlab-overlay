# -*- coding: utf-8 -*-
"""生成 docs/screenshots：压缩版面板与战术图（README 引用）。"""
import os
from PIL import Image
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(BASE, "docs", "screenshots")
os.makedirs(OUT, exist_ok=True)
jobs = [
    (os.path.join(BASE, "out", "overlay", "_p3b", "panel_score_t6.png"), "panel.png", 1280, "PNG"),
    (os.path.join(BASE, "out", "overlay", "_p3c", "giant_arrow_03.png"), "giant_arrow.jpg", 1600, "JPEG"),
    (os.path.join(BASE, "out", "overlay", "_p2", "hudp_t6.png"), "hud.png", 1280, "PNG"),
]
for src, name, width, fmt in jobs:
    if not os.path.exists(src):
        print("MISSING", src)
        continue
    im = Image.open(src).convert("RGB")
    w, h = im.size
    if w > width:
        im = im.resize((width, int(h * width / w)), Image.LANCZOS)
    dst = os.path.join(OUT, name)
    if fmt == "PNG":
        im.save(dst, "PNG", optimize=True)
    else:
        im.save(dst, "JPEG", quality=85, optimize=True)
    print(name, os.path.getsize(dst), "B", im.size)
