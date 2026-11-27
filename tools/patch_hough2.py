# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "grid_hough.py")
t = open(p, encoding="utf-8").read()
t = t.replace("m[:70, :] = 0; m[650:, :] = 0; m[:, :120] = 0; m[:, 1180:] = 0",
              "m[:110, :] = 0; m[630:, :] = 0; m[:, :150] = 0; m[:, 1160:] = 0")
t = t.replace("threshold=60, minLineLength=90, maxLineGap=12", "threshold=80, minLineLength=140, maxLineGap=10")
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("patched2")
