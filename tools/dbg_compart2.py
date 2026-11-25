# -*- coding: utf-8 -*-
import os, sys, json
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab.layout_score import analyze_compartments, load_layout, score_layout

for name in ("01","02","03","04","05","06"):
    d = load_layout(os.path.join(BASE, "bases", "th16", name, "layout.json"))
    grid = int(d.get("grid", 44))
    walls = [(int(x), int(y)) for x, y in (d.get("walls") or [])]
    oob = [w for w in walls if not (0 <= w[0] < grid and 0 <= w[1] < grid)]
    clipped = [w for w in walls if (0 <= w[0] < grid and 0 <= w[1] < grid)]
    c0 = analyze_compartments(grid, walls, d.get("buildings") or [])
    c1 = analyze_compartments(grid, clipped, d.get("buildings") or [])
    print("%s walls=%d oob=%d clipped=%d | comps %d->%d | deadtiles %d->%d | isolated %d->%d" % (
        name, len(walls), len(oob), len(clipped),
        len(c0["compartments"]), len(c1["compartments"]),
        sum(x["tile_count"] for x in c0["compartments"]),
        sum(x["tile_count"] for x in c1["compartments"]),
        c0["isolated_wall_count"], c1["isolated_wall_count"]))
