# -*- coding: utf-8 -*-
import os, json
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
up = os.path.join(BASE, "out", "overlay", "_p3a", "upstream", "clash-of-clans-base-validator-main")
p = os.path.join(up, "coc_base", "art", "manifest.json")
raw = open(p, encoding="utf-8").read()
d = json.loads(raw)
print("calibration:", json.dumps(d.get("calibration"), ensure_ascii=False)[:300])
print("has eagle substring:", "eagle" in raw.lower())
i = raw.lower().find("eagle")
if i >= 0:
    print("context:", raw[max(0, i - 300):i + 500])
kinds = sorted({a.get("kind") for a in d.get("assets", [])})
print("kinds sample:", kinds[:40])
