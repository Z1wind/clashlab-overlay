# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "overlay", "pages.py")
t = open(p, encoding="utf-8").read()
old = '''    imgui.text(f"模式={farm.get('mode') or '-'}  "
               _L(ready, f"实时={'开' if live else '演练'}", f"Live={'on' if live else 'dry'}"))'''
new = '''    imgui.text(_L(ready,
                  f"模式={farm.get('mode') or '-'}  实时={'开' if live else '演练'}",
                  f"Mode={farm.get('mode') or '-'}  Live={'on' if live else 'dry'}"))'''
if old in t:
    t = t.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("syntax fixed")
else:
    print("anchor miss")
