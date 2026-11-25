# -*- coding: utf-8 -*-
import os, sys, json
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, os.path.join(BASE, "out", "tactics", "_convention"))
import check_convention as cc
bases = cc.load_bases()
rows = cc.recount_oob(bases)
flat = []
for chunk in rows:
    if isinstance(chunk, list):
        flat.extend(chunk)
    else:
        flat.append(chunk)
tot = {"A": 0, "B": 0, "C": 0, "all3": 0}
for r in flat:
    for k in ("A", "B", "C"):
        if r.get("oob_" + k):
            tot[k] += 1
    if r.get("oob_A") and r.get("oob_B") and r.get("oob_C"):
        tot["all3"] += 1
print("flat rows", len(flat), "totals", tot)
# 尺寸表来源
for n, v in vars(cc).items():
    if isinstance(v, dict) and "spell-tower" in v:
        print("size table", n, "spell-tower =", v.get("spell-tower"), "eagle =", v.get("eagle-artillery"), "inferno =", v.get("inferno-tower"))
