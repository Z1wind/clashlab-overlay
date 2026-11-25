# -*- coding: utf-8 -*-
import os, json, glob
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
up = os.path.join(BASE, "out", "overlay", "_p3a", "upstream", "clash-of-clans-base-validator-main")
# 找 footprint 定义
hits = []
for p in glob.glob(os.path.join(up, "**", "*.json"), recursive=True):
    try:
        s = open(p, encoding="utf-8").read()
    except Exception:
        continue
    if "spell" in s.lower() and ("footprint" in s or "width" in s or "size" in s):
        hits.append((os.path.relpath(p, up), len(s)))
print("json candidates:", hits[:10])
for rel, _ in hits[:3]:
    d = json.load(open(os.path.join(up, rel), encoding="utf-8"))
    s = json.dumps(d, ensure_ascii=False)
    i = s.lower().find("spell")
    print("==", rel, "context:", s[max(0, i - 300):i + 300])
