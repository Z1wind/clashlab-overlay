# -*- coding: utf-8 -*-
import os, json, sys
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
up = os.path.join(BASE, "out", "overlay", "_p3a", "upstream", "clash-of-clans-base-validator-main")
d = json.load(open(os.path.join(up, "rulesets", "home-2026-11-17.json"), encoding="utf-8"))
print("ruleset keys:", list(d.keys())[:8])
# 找 buildings 字典
def find_buildings(o, depth=0):
    if isinstance(o, dict):
        for k, v in o.items():
            if isinstance(v, dict) and "width" in v and "height" in v:
                return o
            r = find_buildings(v, depth + 1)
            if r is not None:
                return r
    return None
b = find_buildings(d)
if b is None:
    print("no buildings dict found")
else:
    for name in ("spell_tower", "eagle_artillery", "inferno_tower", "air_sweeper", "clan_castle", "firespitter", "ricochet_cannon", "monolith", "scattershot", "multi_archer_tower"):
        if name in b:
            e = b[name]
            print("%-20s width=%s height=%s status=%s" % (name, e.get("width"), e.get("height"), e.get("status")))
        else:
            print("%-20s MISSING" % name)
sys.path.insert(0, BASE)
import clashlab.assets as a
for k in ("spell-tower", "eagle-artillery", "firespitter", "ricochet-cannon", "multi-archer-tower", "monolith", "scattershot"):
    v = a.STATS.get(k) or {}
    print("ours %-20s size=%s" % (k, v.get("size")))
