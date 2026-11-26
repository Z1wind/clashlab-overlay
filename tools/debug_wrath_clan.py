# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat")
from clashlab import cocapi
for q in ("Wrath of Kings", "Wrath of Kings ", "wrath of kings"):
    try:
        r = cocapi.search_clan(q, fresh=True)
        print("clan", repr(q), "->", [(x["name"], x["tag"], x["members"]) for x in r[:5]])
    except Exception as e:
        print("clan", repr(q), "ERR", str(e)[:80])
print("---- members check ----")
for q in ("Wrath of Kings",):
    try:
        cs = cocapi.search_clan(q, fresh=True)
    except Exception as e:
        cs = []
    for c in cs[:3]:
        try:
            w = cocapi.war_members(c["tag"], fresh=True)
        except Exception as e:
            print(c["tag"], "war ERR", str(e)[:60]); continue
        if not w:
            print(c["tag"], "no war"); continue
        names = [m["name"] for side in ("clan", "opponent") for m in w[side]["members"]]
        print(c["tag"], c["name"], w["state"], len(names), "chetzz among:", [n for n in names if "het" in (n or "").lower()][:5])
