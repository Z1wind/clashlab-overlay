# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "topdown.py")
t = open(p, encoding="utf-8").read()
old = '    _text_outline(img, "grid %d  buildings %d  walls %d" % (g, len(buildings), len(walls)),\n                  (margin + 300, 36), 0.42, (170, 186, 204))'
new = '    _text_outline(img, "grid %d  annotated %d  walls %d  (未标注建筑不会显示)" % (g, len(buildings), len(walls)),\n                  (margin + 300, 36), 0.42, (170, 186, 204))'
if old in t:
    t = t.replace(old, new)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("title updated")
else:
    print("title anchor miss")
