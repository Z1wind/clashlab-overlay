# -*- coding: utf-8 -*-
import json, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat")
from clashlab import cocapi
TAG = "#PLVYQ0G2U"; CLAN = "#20R9PL0VU"
w = cocapi.war_members(CLAN, fresh=True)
print("war:", None if not w else (w["state"], "%dv%d" % (w["team_size"], w["team_size"]), w["start_time"], w["end_time"]))
found = None
if w:
    for side in ("clan", "opponent"):
        for m in w[side]["members"]:
            if str(m.get("tag") or "").upper() == TAG.upper() or "shadow" in (m.get("name") or "").lower():
                print("member:", side, m)
                found = found or m
ths = sorted({m["th"] for m in (w["opponent"]["members"] if w else []) if m.get("th")})
if w:
    print("clan members TH:", sorted({m["th"] for m in w["clan"]["members"] if m.get("th")}))
    print("opponent members TH:", ths)
out = {"player_tag": TAG, "clan_tag": CLAN, "war": w, "matched_member": found,
       "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
json.dump(out, open(r"out\live\enemy_war_resolved.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("saved out/live/enemy_war_resolved.json")
