# -*- coding: utf-8 -*-
"""标注自洽性检查：把 67 条标注的每类数量与 TH16 上限对照（上限按游戏常识，标注为 approximate）。"""
import json, os
from collections import Counter
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
HI = os.path.join(BASE, "out", "overlay", "_auto_label", "hi")
rows = []
for fn in ("labels_max.json", "labels_max2.json", "labels_max3.json", "labels_max4.json"):
    p = os.path.join(HI, fn)
    if os.path.exists(p):
        rows += json.load(open(p, encoding="utf-8"))
cnt = Counter(r["type"] for r in rows)
CAP = {"town-hall": 1, "clan-castle": 1, "monolith": 1, "eagle-artillery": 1,
       "multi-archer-tower": 2, "scattershot": 2, "ricochet-cannon": 2, "firespitter": 2,
       "air-sweeper": 2, "spell-tower": 2, "inferno-tower": 3, "bomb-tower": 2,
       "x-bow": 4, "air-defense": 4, "hidden-tesla": 5, "wizard-tower": 5, "mortar": 4,
       "archer-tower": 8, "cannon": 7, "gold-mine": 7, "builder-hut": 5, "barracks": 1}
over = {t: {"labels": cnt[t], "cap": CAP.get(t, "?")} for t in cnt if isinstance(CAP.get(t), int) and cnt[t] > CAP[t]}
total_over = 0
print("type                 labels  cap  verdict")
for t in sorted(cnt):
    cap = CAP.get(t, "?")
    verdict = "OK" if not isinstance(cap, int) or cnt[t] <= cap else "超上限 → 至少 %d 条错标/重复" % (cnt[t] - cap)
    if isinstance(cap, int) and cnt[t] > cap:
        total_over += cnt[t] - cap
    print("%-20s %-6d %-4s %s" % (t, cnt[t], cap, verdict))
print()
print("至少错标/重复条数下限 = %d / %d (%.0f%%)" % (total_over, len(rows), 100.0 * total_over / len(rows)))
json.dump({"labels": len(rows), "counts": dict(cnt), "caps": CAP, "min_wrong": total_over,
           "min_wrong_ratio": total_over / len(rows)},
          open(os.path.join(HI, "label_audit.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
