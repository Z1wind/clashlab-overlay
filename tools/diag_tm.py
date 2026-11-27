# -*- coding: utf-8 -*-
"""诊断：检测点与 GT 的最近距离分布。"""
import json, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
d = json.load(open(BASE + r"\out\layouts_src\tm_eval_b01.json", encoding="utf-8"))
gt = d["gt"]; det = d["detections"]
print("gt sample:", gt[:6])
print("det sample:", [(x["type"], x["tile"], round(x["score"], 2)) for x in det[:8]])
ds = []
for x in det:
    best = min(abs(x["tile"][0]-g[1]) + abs(x["tile"][1]-g[2]) for g in gt)
    ds.append(best)
ds.sort()
print("nearest GT manhattan: min", ds[0], "p25", ds[len(ds)//4], "median", ds[len(ds)//2], "p75", ds[3*len(ds)//4])
