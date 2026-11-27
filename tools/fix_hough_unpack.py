# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "hires_calib_hough.py")
t = open(p, encoding="utf-8").read()
t = t.replace("""    for l in lines[:400]:
        x1, y1, x2, y2 = l[0]""", """    for l in lines[:400]:
        arr = np.asarray(l).reshape(-1)
        if arr.size < 4:
            continue
        x1, y1, x2, y2 = arr[:4]""")
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("patched")
