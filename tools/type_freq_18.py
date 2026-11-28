# -*- coding: utf-8 -*-
"""18 张标注的类型频次统计：找出稀有类型（下一步标注重点）。"""
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DL = os.path.join(os.path.expanduser("~"), "Downloads")
paths = [os.path.join(DL, "annot_b01 (1).json"), os.path.join(DL, "annot_b02 (1).json")]
paths += [os.path.join(DL, "annot_b%02d.json" % i) for i in range(3, 9)]
paths += [os.path.join(DL, "annot_%s.json" % n) for n in
          ("b10","b11","b12","b14","b15","b16","b17","b18","b19","b20")]
cnt = {}
files = 0
for p in paths:
    if not os.path.exists(p): continue
    d = json.load(open(p, encoding="utf-8")); files += 1
    for x in d.get("buildings") or []:
        cnt[x["type"]] = cnt.get(x["type"], 0) + 1
print("bases", files, "types", len(cnt), "total", sum(cnt.values()))
print("\n稀有类型（<10 例）：")
for t, c in sorted(cnt.items(), key=lambda kv: kv[1]):
    if c < 10: print("  %-22s %d" % (t, c))
print("\n最多：", ", ".join("%s=%d" % kv for kv in sorted(cnt.items(), key=lambda kv: -kv[1])[:5]))
