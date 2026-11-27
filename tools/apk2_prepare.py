# -*- coding: utf-8 -*-
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import Image
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(BASE, "android", "assets", "img")
pairs = [("enemy_scout_live.png", "w1.png"), ("scouts\\map_01.png", "w2.png"), ("scouts\\war_01_LR8GVY892.png", "w3.png")]
for src, dst in pairs:
    p = os.path.join(BASE, "out", "live", src)
    im = Image.open(p).convert("RGB"); im.thumbnail((1600, 1600))
    q = os.path.join(OUT, dst); im.save(q, "PNG", optimize=True)
    print(dst, im.size, os.path.getsize(q))

# MainActivity: 加载新的标注页
p = os.path.join(BASE, "android", "java", "com", "clashlab", "annotator", "MainActivity.java")
t = open(p, encoding="utf-8").read()
t = t.replace('file:///android_asset/index.html', 'file:///android_asset/annotate2.html')
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("MainActivity -> annotate2.html")
