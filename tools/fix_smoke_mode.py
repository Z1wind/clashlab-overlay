# -*- coding: utf-8 -*-
import os, re
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "desktop_app.py")
t = open(p, encoding="utf-8").read()
t = t.replace("    if smoke:\n", "    if smoke == 1:\n", 1)
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("smoke mode fixed")
