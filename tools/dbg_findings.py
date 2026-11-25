# -*- coding: utf-8 -*-
import sys, traceback
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab import layout_score
lay = {"name": "t", "grid": 44, "walls": [],
       "buildings": [{"type": "town-hall", "tile": [21, 21]},
                     {"type": "cannon", "tile": [25, 25]},
                     {"type": "archer-tower", "tile": [17, 27]}]}
try:
    r = layout_score.score_layout(lay)
    print("metrics:", [(m["id"], m["score"]) for m in r["metrics"]])
except Exception:
    traceback.print_exc()
from clashlab import defense_findings as df
try:
    print("findings:", df.findings(lay))
except Exception:
    traceback.print_exc()
