# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tests", "test_cocapi.py")
t = open(p, encoding="utf-8").read()
t = t.replace("cocapi.player_war_attacks = lambda tag: PLAYER_ITEMS",
              "cocapi.player_war_attacks = lambda tag, **kw: PLAYER_ITEMS")
t = t.replace("cocapi.player_war_attacks = lambda tag: []",
              "cocapi.player_war_attacks = lambda tag, **kw: []")
t = t.replace("cocapi.clan_wars = lambda tag: [WAR]",
              "cocapi.clan_wars = lambda tag, **kw: [WAR]")
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("tests patched")
