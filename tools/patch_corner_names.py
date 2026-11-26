# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "label_corners", "start.py")
t = open(p, encoding="utf-8").read()
old = '        out.append({"file": name, "name": os.path.basename(p), "done": done,'
new = '        display = name.split("/")[-2] + "/" + os.path.basename(p) if "bases/" in name else os.path.basename(p)\n        out.append({"file": name, "name": display, "done": done,'
if "display = name.split" in t:
    print("already patched")
else:
    t = t.replace(old, new)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("patched start.py")
