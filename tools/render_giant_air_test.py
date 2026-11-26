# -*- coding: utf-8 -*-
import json, os, sys
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab.overlay import giant_arrow_diagram as g

lay = json.load(open(os.path.join(BASE, "bases", "th16", "03", "layout.json"), encoding="utf-8"))
picks = []
want = ("air-defense", "air-sweeper", "hidden-tesla")
for b in lay["buildings"]:
    if b["type"] in want and len([p for p in picks if p["type"] == b["type"]]) < 2:
        picks.append({"type": b["type"], "tile": b["tile"]})
print("picked:", picks)
plan = {"goal": "测试穿云箭对空目标", "model": "local",
        "phases": [{"name": "穿云箭", "units": [{"type": "giant-arrow", "drop_tile": [0, 21]}], "route": [[0, 21], [43, 21]],
                    "targets": [p["tile"] for p in picks], "purpose": "清吹风机与防空火箭"}]}
out = os.path.join(BASE, "out", "giant_arrow_air_test.png")
im = g.render_giant_arrow_diagram(lay, plan, out, base=os.path.join(BASE, "bases", "th16", "03", "base.png"))
print("rendered:", out, im.size)
spec = g.giant_arrow_spec(plan)
hits = g.match_skewered(lay, spec["from"], spec["to"]) if spec else []
print("hits:", [(h["type"], h["tile"], h["air"], h["hidden"]) for h in hits])
print("summary:", g.summarize_hits(hits))
