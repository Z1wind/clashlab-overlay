# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "overlay_exe_main.py")
t = open(p, encoding="utf-8").read()
old = ("        if a.mode is None:\n"
       "            a.mode = 'PANEL'\n")
new = ("        if a.mode is None:\n"
       "            a.mode = 'PANEL'\n"
       "        if not a.allow_primary:\n"
       "            a.allow_primary = True  # 双击在单屏/主屏也可见（否则被主屏守卫隐藏）\n")
if old in t and "双击在单屏" not in t:
    t = t.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("bare launch allow_primary")
else:
    print("anchor miss/already")
