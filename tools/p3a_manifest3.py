# -*- coding: utf-8 -*-
import os, json
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
up = os.path.join(BASE, "out", "overlay", "_p3a", "upstream", "clash-of-clans-base-validator-main")
d = json.load(open(os.path.join(up, "coc_base", "art", "manifest.json"), encoding="utf-8"))
assets = d.get("assets")
print("assets type", type(assets).__name__, "len", len(assets))
rows = []
if isinstance(assets, list):
    for a in assets:
        n = str(a.get("kind", ""))
        if any(k in n for k in ("eagle", "spell_tower", "inferno", "clan_castle", "firespitter", "monolith")):
            rows.append((n, a.get("level"), a.get("width_tiles"), a.get("width"), a.get("height"), a.get("bounds")))
elif isinstance(assets, dict):
    for n, a in assets.items():
        if any(k in n for k in ("eagle", "spell_tower", "inferno", "clan_castle", "firespitter", "monolith")):
            rows.append((n, a.get("level"), a.get("width_tiles"), a.get("width"), a.get("height"), a.get("bounds")))
for r in sorted(rows):
    print("%-26s lvl=%-2s tiles=%-6s px=%sx%s bounds=%s" % r)
