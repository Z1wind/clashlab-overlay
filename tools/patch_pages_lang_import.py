# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "overlay", "pages.py")
t = open(p, encoding="utf-8").read()
if "from . import lang" not in t.split("def ")[0]:
    # 在模块导入区加 lang
    anchor = "from . import draw as _hud_draw"
    if anchor in t:
        t = t.replace(anchor, anchor + "\nfrom . import lang", 1)
        open(p, "w", encoding="utf-8", newline="\n").write(t)
        print("lang imported at module level")
    else:
        print("anchor miss: import")
