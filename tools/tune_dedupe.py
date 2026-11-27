# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "auto_candidates.py")
t = open(p, encoding="utf-8").read()
old = '''    picked = []
    for it in items:
        if all(abs(it["tile"][0] - p["tile"][0]) > max(1, it["size"] // 2) or
               abs(it["tile"][1] - p["tile"][1]) > max(1, it["size"] // 2) for p in picked):
            picked.append(it)'''
new = '''    picked = []
    for it in items:
        sep = max(1.2, it["size"] * 0.6)  # 允许相邻建筑（间距 2 格）保留
        if all(abs(it["tile"][0] - p["tile"][0]) >= sep or
               abs(it["tile"][1] - p["tile"][1]) >= sep for p in picked):
            picked.append(it)'''
if old in t:
    t = t.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("dedupe tuned")
else:
    print("dedupe anchor miss")
