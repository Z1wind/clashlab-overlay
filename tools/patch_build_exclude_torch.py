# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
BT = chr(96)
p = os.path.join(BASE, "build_overlay.ps1")
t = open(p, encoding="ascii", errors="ignore").read()
if "--exclude-module torch" not in t:
    anchor = "    --hidden-import clashlab.cocapi " + BT
    add = ("\r\n    --exclude-module torch " + BT +
           "\r\n    --exclude-module torchvision " + BT +
           "\r\n    --exclude-module torchaudio " + BT +
           "\r\n    --exclude-module sympy " + BT +
           "\r\n    --exclude-module networkx " + BT +
           "\r\n    --exclude-module matplotlib " + BT)
    t = t.replace(anchor, anchor + add, 1)
    open(p, "w", encoding="ascii", newline="").write(t)
    print("excludes added")
else:
    print("already")
