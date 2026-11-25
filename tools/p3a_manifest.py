# -*- coding: utf-8 -*-
import os, json
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
up = os.path.join(BASE, "out", "overlay", "_p3a", "upstream", "clash-of-clans-base-validator-main")
man = json.load(open(os.path.join(up, "coc_base", "art", "manifest.json"), encoding="utf-8"))
items = man.get("items") or man.get("objects") or man.get("art") or []
if isinstance(man, dict) and not isinstance(items, list):
    for k, v in man.items():
        if isinstance(v, list):
            items = v
            break
print("manifest entries:", len(items) if isinstance(items, list) else "?")
want = ("eagle_artillery", "eagle-artillery", "spell_tower", "spell-tower", "firespitter", "inferno_tower", "clan_castle")
for it in items if isinstance(items, list) else []:
    kind = str(it.get("kind", ""))
    if any(w.strip("-").replace("-", "_") in kind for w in want):
        print("%-24s level=%-2s width_tiles=%s size=%sx%s" % (kind, it.get("level"), it.get("width_tiles"), it.get("width"), it.get("height")))
