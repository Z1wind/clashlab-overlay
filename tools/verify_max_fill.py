# -*- coding: utf-8 -*-
import json, sys, os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab import wargame, th_data, levels

d = json.load(open(os.path.join(BASE, "out", "annotate", "03_annotated.json"), encoding="utf-8"))
lv = [(b["type"], b.get("level")) for b in d["buildings"]]
print("03 前 8 栋:", lv[:8])
print("有 level 的栋数:", sum(1 for b in d["buildings"] if b.get("level")))
# 每种类型满级值
seen = {}
for t, l in lv:
    seen.setdefault(t, set()).add(l)
for t in ("cannon", "x-bow", "town-hall", "monolith", "air-defense", "scattershot"):
    print(t, "->", sorted(seen.get(t, [])))
# wargame 能读到 level
L = wargame.parse_layout(os.path.join(BASE, "out", "annotate", "03_annotated.json"))
print("parse_layout 建筑:", len(L.buildings), "| 首栋 level:", L.buildings[0].get("level"),
      "hp:", round(L.buildings[0]["hp"], 1))
# 满级 vs 低等级对比（同一阵）
lay = json.load(open(os.path.join(BASE, "out", "annotate", "03_annotated.json"), encoding="utf-8"))
import copy
low = copy.deepcopy(lay)
for b in low["buildings"]:
    b["level"] = max(1, int((b.get("level") or 10) * 0.4))
a = wargame.simulate_once(lay, {"giant": 8}, spawn=(2, 10), seed=1, collect_events=False)
b2 = wargame.simulate_once(low, {"giant": 8}, spawn=(2, 10), seed=1, collect_events=False)
print("满级阵摧毁:", a["destruction"], "| 低等级阵摧毁:", b2["destruction"])
