# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "grid_hough.py")
t = open(p, encoding="utf-8").read()
t = t.replace("    for x1, y1, x2, y2 in lines[:, 0]:", "    for x1, y1, x2, y2 in lines.reshape(-1, 4):")
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("patched")
