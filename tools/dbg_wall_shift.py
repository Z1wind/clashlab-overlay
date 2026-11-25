# -*- coding: utf-8 -*-
import os, sys, json
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab.layout_score import load_layout, wall_ring_coverage, footprint_bounds

for name in ("01","02","03","04","05","06"):
    d = load_layout(os.path.join(BASE, "bases", "th16", name, "layout.json"))
    grid = int(d.get("grid", 44))
    th = next(b for b in d["buildings"] if b.get("type") == "town-hall")
    walls = [(int(x), int(y)) for x, y in (d.get("walls") or [])]
    best = (-1, None)
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            shifted = [(x + dx, y + dy) for x, y in walls]
            c = wall_ring_coverage(th, shifted, grid)
            if c > best[0]:
                best = (c, (dx, dy))
    print("%s TH tile=%s  best_ring=%.2f at shift=%s" % (name, th.get("tile"), best[0], best[1]))
