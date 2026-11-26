# -*- coding: utf-8 -*-
import glob, json, os, sys
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab import assets, levels
from collections import Counter
cnt = Counter(); none_cnt = Counter(); unknown = set()
for p in sorted(glob.glob(os.path.join(BASE, "out", "annotate", "*_annotated.json"))):
    d = json.load(open(p, encoding="utf-8"))
    for b in d.get("buildings") or []:
        t = str(b.get("type") or "")
        cnt[t] += 1
        if not b.get("level"):
            none_cnt[t] += 1
            if t not in assets.STATS and t not in (getattr(assets, "TH16_OVERRIDE", {}) or {}):
                unknown.add(t)
print("类型分布:", dict(cnt))
print("缺 level 的类型:", dict(none_cnt))
print("不在 assets 里的新类型:", sorted(unknown))
# 这些新类型 max level 能从 ruleset 查到吗
for t in sorted(unknown):
    print(t, "max_level_of:", levels.max_level_of(t, 16))
