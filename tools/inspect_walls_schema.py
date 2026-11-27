# -*- coding: utf-8 -*-
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
lay = json.load(open(os.path.join(BASE, "out", "annotate", "01_annotated.json"), encoding="utf-8"))
print("top keys:", list(lay.keys()))
w = lay.get("walls")
print("walls type:", type(w).__name__, "len:", len(w) if w is not None else None)
print("walls sample:", json.dumps(w[:2], ensure_ascii=False)[:400] if w else w)
from clashlab.layout_grid import LayoutGrid
g = LayoutGrid.from_layout(lay)
print("wall_count:", g.wall_count(), "buildings:", g.building_count(), "comps:", len(g.compartments()))
