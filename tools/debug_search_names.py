# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat")
from clashlab import cocapi
for q in ("MH Tipu", "Mh Tipu", "MH TIPU", "Tipu"):
    try:
        r = cocapi.search_player(q, fresh=True)
        print("player search", repr(q), "->", [(x["name"], x["tag"], x["th"], (x["clan"] or {}).get("name")) for x in r[:6]])
    except Exception as e:
        print("player search", repr(q), "ERR", str(e)[:60])
for q in ("baby warrior", "babY WaRioR", "baby warior", "baby"):
    try:
        r = cocapi.search_clan(q, fresh=True)
        print("clan search", repr(q), "->", [(x["name"], x["tag"], x["members"]) for x in r[:6]])
    except Exception as e:
        print("clan search", repr(q), "ERR", str(e)[:60])
