# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "overlay", "pages.py")
t = open(p, encoding="utf-8").read()
bad = '''    from . import draw as _hud_draw
from . import lang
    _hud_draw.mark_panel_open()'''
good = '''    from . import draw as _hud_draw
    _hud_draw.mark_panel_open()'''
if bad in t:
    t = t.replace(bad, good, 1)
    print("removed bad inner import")
if "from . import lang" not in t.split("def ")[0]:
    t = t.replace("from . import theme", "from . import theme\nfrom . import lang", 1)
    print("module import added")
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("done")
