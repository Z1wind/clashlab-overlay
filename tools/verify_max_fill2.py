# -*- coding: utf-8 -*-
import copy, json, os, sys
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab import wargame

lay = json.load(open(os.path.join(BASE, "out", "annotate", "03_annotated.json"), encoding="utf-8"))
print("levels sample:", [(b["type"], b.get("level")) for b in lay["buildings"][:6]])
L = wargame.parse_layout(lay)
print("parse_layout level:", [(b["type"], b.get("level")) for b in L.buildings[:6]])

low = copy.deepcopy(lay)
for b in low["buildings"]:
    b["level"] = max(1, int(round((b.get("level") or 10) * 0.4)))

full_res = wargame.run(lay, {"giant": 10, "wizard": 12}, trials=20, seed=1, workers=1)
low_res = wargame.run(low, {"giant": 10, "wizard": 12}, trials=20, seed=1, workers=1)
low_troop = wargame.run(lay, {"giant": 10, "wizard": 12}, trials=20, seed=1, workers=1,
                        troop_levels={"giant": 3, "wizard": 3}, hero_levels={"queen": 10, "king": 10})
print("A 满级阵:", full_res["destruction"])
print("B 低等级阵(40%):", low_res["destruction"])
print("C 满级阵+低配兵:", low_troop["destruction"])
