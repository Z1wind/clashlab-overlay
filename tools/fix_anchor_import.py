# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "anchor_calib.py")
t = open(p, encoding="utf-8").read()
t = t.replace("import glob, json, re, sys", "import glob, json, os, re, sys", 1)
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("os imported")
