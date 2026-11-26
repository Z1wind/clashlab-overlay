# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat")
from clashlab import cocapi
for q in ("MH Tipu", "Mh Tipu", "MH TIPU"):
    try:
        r = cocapi.search_player(q, fresh=True)
        print("player", repr(q), "->", [(x["name"], x["tag"], x["th"], (x["clan"] or {}).get("name"), (x["clan"] or {}).get("tag")) for x in r[:8]])
    except Exception as e:
        print("player", repr(q), "ERR", type(e).__name__, str(e)[:80])
print("---- resolve ----")
r = cocapi.resolve_opponent("Mh Tipu", "babY WaRioR", fresh=True, ocr_level="16.")
print({k: r.get(k) for k in ("player", "clan", "match", "fresh")})
