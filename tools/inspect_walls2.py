# -*- coding: utf-8 -*-
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab.layout_grid import LayoutGrid, _polyline_points
for f in ("01_annotated.json", "06_annotated.json"):
    lay = json.load(open(os.path.join(BASE, "out", "annotate", f), encoding="utf-8"))
    pts = _polyline_points(lay.get("walls"))
    g = LayoutGrid.from_layout(lay)
    print(f, "| wall pts:", len(pts), "| wall tiles:", g.wall_count(), "| comps:", len(g.compartments()))
    if pts:
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        print("   bbox:", (min(xs), min(ys)), (max(xs), max(ys)))
        print("   first pts:", pts[:6])
