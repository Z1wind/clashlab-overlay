# -*- coding: utf-8 -*-
import json, os, sys
sys.path.insert(0, r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat")
from clashlab import wargame
lay = os.path.join(r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat", "bases", "th16", "03", "layout.json")
res = wargame.run(lay, {"giant": 8, "wizard": 12, "queen": 1}, trials=40, seed=3)
print(json.dumps(res, ensure_ascii=False)[:900])
print("--- single ---")
one = wargame.simulate_once(lay, {"giant": 5, "wizard": 8}, spawn=(1, 22), max_time=90, tick=0.25)
print({k: one[k] for k in ("time", "units_alive", "buildings_destroyed", "buildings_total", "destruction", "hp_destroyed")})
print("walls:", one["walls"])
print("events head:", one["events"][:3], "... end:", one["events"][-1])
