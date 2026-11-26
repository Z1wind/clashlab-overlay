# -*- coding: utf-8 -*-
import json, os, sys
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab.overlay import giant_arrow_diagram as g
lay = json.load(open(os.path.join(BASE, "out", "annotate", "01_annotated.json"), encoding="utf-8"))
teslas = [b for b in lay["buildings"] if b["type"] == "hidden-tesla"]
print("teslas:", [b["tile"] for b in teslas][:5])
best = g.optimize_giant_arrow(lay, top=3)["best"]
print("best:", best["from"], "->", best["to"], "score", best["score"], best["summary"])
plan = {"goal": "特斯拉隐身提醒验证", "phases": [{"name": "穿云箭",
        "units": [{"type": "giant-arrow", "drop_tile": best["from"]}],
        "route": [best["from"], best["to"]],
        "targets": [h["tile"] for h in best["hits"]],
        "purpose": "优先吹风机/防空火箭"}]}
out = os.path.join(BASE, "out", "giant_arrow_tesla_warning.png")
g.render_giant_arrow_diagram(lay, plan, out, base=os.path.join(BASE, "bases", "th16", "01", "base.png"))
print("rendered:", out)
