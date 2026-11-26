# -*- coding: utf-8 -*-
import json, os, sys
sys.path.insert(0, r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat")
from clashlab import wargame
lay = os.path.join(r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat", "bases", "th16", "03", "layout.json")
res = wargame.run(lay, {"giant": 8, "wizard": 12, "earthquake": 2}, trials=40, seed=3)
print("MC keys:", list(res.keys()))
print("destruction:", res["destruction"])
print("best:", res["best"])
print("timeline len:", len(res.get("timeline") or []))
one = wargame.simulate_once(lay, {"giant": 5, "wizard": 8}, spawn=(1, 22), max_time=90, tick=0.25)
print("single:", {k: one[k] for k in ("time", "units_alive", "buildings_destroyed", "buildings_total", "destruction", "hp_destroyed")})
print("walls:", one["walls"])
