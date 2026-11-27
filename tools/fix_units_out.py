# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "build_units_page.py")
t = open(p, encoding="utf-8").read()
if 'out = os.path.join(BASE, "out", "units.html")' not in t:
    t = t.replace('open(out, "w", encoding="utf-8", newline="\\n").write(html)',
                  'out = os.path.join(BASE, "out", "units.html")\nopen(out, "w", encoding="utf-8", newline="\\n").write(html)')
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("out var restored")
