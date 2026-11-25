# -*- coding: utf-8 -*-
import os, json
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "out", "overlay", "_p3b", "walls_extracted", "_metrics.json")
d = json.load(open(p, encoding="utf-8"))
print("base  kind            oldW iso%  ring  comp  dead | newW iso%  ring  comp  dead  closedW")
for b, v in d["bases"].items():
    m = v["metrics"]; o = m["old"]; n = m["new"]
    kind = v["meta"]["homography"].get("kind", "?")
    print("%s  %-14s %4d %5.1f %5.2f %5d %5d | %4d %5.1f %5.2f %5d %5d %6d" % (
        b, kind, o["wall_count"], 100*o["isolated_ratio"], o["th_ring_coverage"], o["compartment_count"], o["dead_zone_count"],
        n["wall_count"], 100*n["isolated_ratio"], n["th_ring_coverage"], n["compartment_count"], n["dead_zone_count"],
        v["counts"]["closed_variant_cells"]))
