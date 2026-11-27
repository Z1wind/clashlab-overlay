# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "centernet_fast.py")
t = open(p, encoding="utf-8").read()
old = '''KEY = ["air-defense", "air-sweeper", "monolith", "eagle_artillery", "scattershot", "town_hall",
       "x-bow", "inferno_tower", "wizard_tower", "cannon", "archer_tower", "mortar",
       "clan_castle", "spell_tower", "bomb_tower", "multi-archer_tower", "hidden_tesla"]
KEY = [k for k in KEY if k in ALL]
IDX = {ALL.index(k): i for i, k in enumerate(KEY)}'''
new = '''WANT = {"air_defense", "air_sweeper", "monolith", "eagle_artillery", "scattershot", "town_hall",
        "x-bow", "inferno_tower", "wizard_tower", "cannon", "archer_tower", "mortar",
        "clan_castle", "spell_tower", "bomb_tower", "multi-archer_tower", "hidden_tesla"}
KEY = [k for k in ALL if k in WANT]
IDX = {ALL.index(k): i for i, k in enumerate(KEY)}'''
if old in t:
    t = t.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("KEY fixed")
else:
    print("anchor miss")
