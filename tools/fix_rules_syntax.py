# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "layout_rules.py")
t = open(p, encoding="utf-8").read()
old = "    edge_storages = [p for p in sum(bmap.get(t, []) for t in STORAGE, []) if min(p[0], p[1], 44 - p[0], 44 - p[1]) <= 3]"
new = "    _all_storages = []\n    for _t in STORAGE:\n        _all_storages.extend(bmap.get(_t) or [])\n    edge_storages = [p for p in _all_storages if min(p[0], p[1], 44 - p[0], 44 - p[1]) <= 3]"
if old in t:
    t = t.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("fixed generator")
else:
    print("anchor miss")
