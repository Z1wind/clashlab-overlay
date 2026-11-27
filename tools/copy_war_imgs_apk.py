# -*- coding: utf-8 -*-
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import Image
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(BASE, "android", "assets", "img")
os.makedirs(OUT, exist_ok=True)
srcs = [("enemy_scout_live.png", "w1.png"), ("map_01.png", "w2.png"), ("war_01_LR8GVY892.png", "w3.png")]
for src, dst in srcs:
    p = os.path.join(BASE, "out", "live", src)
    if not os.path.exists(p):
        print("MISS", src); continue
    im = Image.open(p).convert("RGB")
    im.thumbnail((1600, 1600))
    q = os.path.join(OUT, dst)
    im.save(q, "PNG", optimize=True)
    print(dst, im.size, os.path.getsize(q), "bytes")
