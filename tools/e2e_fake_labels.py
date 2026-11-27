# -*- coding: utf-8 -*-
"""E2E 测试：伪造 labels → layout → 报告（验证下游链路）。"""
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
meta = json.load(open(os.path.join(BASE, "out", "labels", "war", "base_01_205237_candidates.json"), encoding="utf-8"))
items = meta.get("items") or []
types = ["inferno-tower", "x-bow", "air-defense", "eagle-artillery", "scattershot",
         "monolith", "wizard-tower", "cannon", "archer-tower", "mortar"]
labels = {"quad": meta["quad"], "items": []}
for i, it in enumerate(items):
    labels["items"].append({"image": meta["image"], "tile": it["tile"], "size": it.get("size", 2),
                            "type": types[i % len(types)]})
lp = os.path.join(BASE, "out", "labels", "fake_labels_e2e.json")
json.dump(labels, open(lp, "w", encoding="utf-8"), ensure_ascii=False)
from tools.labels_to_layout import convert
lay = convert(lp, "e2e_auto", os.path.join(BASE, "out", "annotate", "e2e_auto.json"))
print("layout:", lay)
from clashlab import battle_report
rep = battle_report.build(lay["path"], th=15)
print("report:", rep["path"], rep["bytes"], "bytes grade", rep["grade"], rep["score"])
