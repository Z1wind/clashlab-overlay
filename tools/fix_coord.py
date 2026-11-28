# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "build_desktop_v2.py")
t = open(p, encoding="utf-8").read()
old = "txt='格 '+Math.floor(uv[0])+','+Math.floor(uv[1]);"
new = "txt='格 '+Math.floor(uv[0]*44)+','+Math.floor(uv[1]*44);"
if old in t:
    t = t.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("coord fix applied")
else:
    print("coord anchor miss")
