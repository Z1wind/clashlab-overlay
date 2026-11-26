# -*- coding: utf-8 -*-
import glob, json, os, sys, time
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab import wargame

for p in sorted(glob.glob(os.path.join(BASE, "out", "annotate", "*_annotated.json"))):
    d = json.load(open(p, encoding="utf-8"))
    lv = [b.get("level") for b in d["buildings"]]
    print(os.path.basename(p), "buildings:", len(lv), "level range:", min(lv), "-", max(lv),
          "missing:", sum(1 for x in lv if not x))
    L = wargame.parse_layout(p)
    print("   parse_layout:", len(L.buildings), "| sample levels:",
          [(b["type"], b.get("level")) for b in L.buildings[:4]])

# 01 阵跑一次 MC（86 栋）
t0 = time.time()
res = wargame.run(os.path.join(BASE, "out", "annotate", "01_annotated.json"),
                  {"giant": 8, "wizard": 10}, trials=10, seed=1, workers=1)
print("01 run:", res["destruction"], "| best:", res["best"], "| elapsed", round(time.time() - t0, 2))
