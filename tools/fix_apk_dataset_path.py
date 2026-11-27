# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "apk_export_to_dataset.py")
t = open(p, encoding="utf-8").read()
old = """    img_path = os.path.join(img_root, base["image"].replace("img/", "")
                            if base["image"].startswith("img/") else base["image"])"""
new = """    rel = base["image"]
    if rel.startswith("img/"):
        rel = rel
    img_path = os.path.join(img_root, rel)"""
if old in t:
    t = t.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("path fixed")
else:
    print("anchor miss")
