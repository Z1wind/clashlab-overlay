# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "overlay", "pages.py")
t = open(p, encoding="utf-8").read()
old = '''        layout = getattr(state, "Layout", None)'''
new = '''        layout = getattr(state, "layout", None)
        if not isinstance(layout, dict):
            layout = getattr(state, "Layout", None)'''
if old in t and 'getattr(state, "layout", None)' not in t.replace(old, ""):
    t = t.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("layout attr compatible patch")
else:
    print("already or anchor miss")
