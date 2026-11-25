# -*- coding: utf-8 -*-
import os, json
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
up = os.path.join(BASE, "out", "overlay", "_p3a", "upstream", "clash-of-clans-base-validator-main")
p = os.path.join(up, "coc_base", "art", "manifest.json")
d = json.load(open(p, encoding="utf-8"))
print("top type", type(d).__name__, "keys", list(d.keys())[:10] if isinstance(d, dict) else len(d))
def walk(o, depth=0):
    if depth > 2:
        return
    if isinstance(o, dict):
        for k, v in list(o.items())[:5]:
            print("  " * depth + f"{k}: {type(v).__name__}" + (f" len={len(v)}" if isinstance(v, (list, dict)) else f" = {str(v)[:60]}"))
            walk(v, depth + 1)
    elif isinstance(o, list) and o:
        print("  " * depth + f"[0] {type(o[0]).__name__}")
        walk(o[0], depth + 1)
walk(d)
# 直接在原文里找 eagle
raw = open(p, encoding="utf-8").read()
i = raw.find("eagle")
print("eagle context:", raw[max(0, i - 200):i + 400])
