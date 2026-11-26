# -*- coding: utf-8 -*-
import glob, json, os, sys
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab import wargame
tot = 0; miss = 0
for p in sorted(glob.glob(os.path.join(BASE, "out", "annotate", "*_annotated.json"))):
    d = json.load(open(p, encoding="utf-8"))
    bs = d.get("buildings") or []
    tot += len(bs)
    miss += sum(1 for b in bs if not b.get("level"))
    print(os.path.basename(p), len(bs))
print("TOTAL:", tot, "missing level:", miss)
res = wargame.run(os.path.join(BASE, "out", "annotate", "04_annotated.json"),
                  {"giant": 10, "wizard": 12}, trials=20, seed=1, workers=1)
print("04 run:", res["destruction"], "best:", res["best"])
