# -*- coding: utf-8 -*-
import os, sys, json
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab.layout_score import analyze_compartments, load_layout

for name in ("03", "05", "06"):
    d = load_layout(os.path.join(BASE, "bases", "th16", name, "layout.json"))
    grid = int(d.get("grid", 44))
    c = analyze_compartments(grid, d.get("walls") or [], d.get("buildings") or [])
    print(name, "grid", grid, "walls", c["wall_count"], "isolated", c["isolated_wall_count"],
          "comps", len(c["compartments"]),
          "deadtiles", sum(x["tile_count"] for x in c["compartments"]))
    # 直接统计：从边界 flood 后仍未达的非墙格数
    wallset = {(int(x), int(y)) for x, y in (d.get("walls") or [])}
    print("   wall x range", min(x for x, _ in wallset) if wallset else None, max(x for x, _ in wallset) if wallset else None,
          "y range", min(y for _, y in wallset) if wallset else None, max(y for _, y in wallset) if wallset else None)
    print("   note:", (d.get("note") or "")[:120])
