# -*- coding: utf-8 -*-
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
p = r"out\live\enemy_live.json"
d = json.load(open(p, encoding="utf-8"))
print("fetched_at:", d.get("fetched_at"))
print("ocr:", {k: d["ocr"].get(k) for k in ("level", "name", "clan")})
print("player:", d["api"].get("player"))
print("match:", d["api"].get("match"))
w = d["api"].get("war")
if w:
    print("war:", w["state"], "%dv%d" % (w["team_size"], w["team_size"]))
    for side in ("clan", "opponent"):
        ms = w[side]["members"]
        print(" ", side, len(ms), "TH:", sorted({m["th"] for m in ms}))
