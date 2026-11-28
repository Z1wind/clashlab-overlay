# -*- coding: utf-8 -*-
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DL = os.path.join(os.path.expanduser("~"), "Downloads")
sets = {}
for i in range(1, 9):
    d = json.load(open(os.path.join(DL, "annot_b%02d.json" % i), encoding="utf-8"))
    sets[i] = {b["type"] for b in d["buildings"]}
    print(i, "types", len(sets[i]))
print("\nb01-only:", sorted(sets[1]-sets[6]))
print("\nb06-only:", sorted(sets[6]-sets[1]))
for i in range(1, 9):
    print(i, "has town-hall:", "town-hall" in sets[i], "| first 6 types:", sorted(sets[i])[:6])
