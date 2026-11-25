# -*- coding: utf-8 -*-
import os, json, sys
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
up = os.path.join(BASE, "out", "overlay", "_p3a", "upstream", "clash-of-clans-base-validator-main")
d = json.load(open(os.path.join(up, "rulesets", "home-2026-11-17.json"), encoding="utf-8"))
objs = d.get("objects", {})
print("objects:", len(objs), "sample keys:", list(objs.keys())[:12])
for name, e in objs.items():
    if not isinstance(e, dict):
        continue
    if any(k in name for k in ("spell", "eagle", "inferno", "sweeper", "castle", "fire", "ricochet", "monolith", "scatter", "archer_tower")):
        print("%-24s w=%s h=%s status=%s" % (name, e.get("width"), e.get("height"), e.get("status")))
print("board:", json.dumps(d.get("board"), ensure_ascii=False)[:200])
sys.path.insert(0, BASE)
from clashlab import segment
for n in dir(segment):
    v = getattr(segment, n)
    if isinstance(v, dict) and "firespitter" in json.dumps(v)[:2000]:
        print("segment table:", n)
        print(json.dumps({k: v[k] for k in list(v)[:20]}, ensure_ascii=False)[:800])
