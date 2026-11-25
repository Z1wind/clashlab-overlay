# -*- coding: utf-8 -*-
import os, sys, json
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, os.path.join(BASE, "out", "tactics", "_convention"))
import check_convention as cc
bases = cc.load_bases()
rows = cc.recount_oob(bases)
tot = {"A": 0, "B": 0, "C": 0, "all3": 0}
per = {}
for r in rows:
    per.setdefault(r.get("base", "?"), {"A": 0, "B": 0, "C": 0, "all3": 0})
    for k in ("A", "B", "C"):
        if r.get(k):
            tot[k] += 1
            per[r.get("base", "?")][k] += 1
    if r.get("A") and r.get("B") and r.get("C"):
        tot["all3"] += 1
        per[r.get("base", "?")]["all3"] += 1
print("rows", len(rows), "totals", tot)
for b in sorted(per):
    print(b, per[b])
json.dump({"totals": tot, "per_base": per, "rows": len(rows)},
          open(os.path.join(BASE, "out", "tactics", "_convention", "recount_after_fix.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
