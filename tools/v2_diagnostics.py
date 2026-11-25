# -*- coding: utf-8 -*-
"""v2 诊断：官方投影帧（gold H）下最近邻配对，输出类型混淆 top5 + FP 类型分布。
只读，不改 gold/候选；阈值取 ≤2.0 格（宽于 1.5 主口径，仅供混淆参考）。"""
import os, sys, json, math
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from clashlab.geo import Calib

gold = json.load(open(os.path.join(ROOT, "out/snap/gold/home_village_gold.json"), encoding="utf-8"))
cand = json.load(open(os.path.join(ROOT, "out/check_verify/home_village/layout_candidates.json"), encoding="utf-8"))
cal = Calib.from_dict(gold["calib"])

G = [(b["id"], b["type"], b["tile"]) for b in gold["buildings"]]
C = []
for x in cand["candidates"] + cand["low_confidence"]:
    box = x.get("box_px")
    if not box:
        continue
    cx, cy = box[0] + box[2] / 2, box[1] + box[3] / 2
    tx, ty = cal.px_to_tile(cx, cy)
    C.append({"type": x["type"], "tier": x.get("tier", "low"), "tile": [tx, ty]})

# gold -> nearest candidate
pairs = []
for gid, gtype, gtile in G:
    best = None
    for c in C:
        d = math.hypot(c["tile"][0] - gtile[0], c["tile"][1] - gtile[1])
        if best is None or d < best[0]:
            best = (d, c)
    if best and best[0] <= 2.0:
        pairs.append((gid, gtype, best[1]["type"], best[1]["tier"], round(best[0], 2)))

from collections import Counter
conf = Counter()
for gid, gt, ct, tier, d in pairs:
    if gt != ct:
        conf[(gt or "unknown", ct)] += 1
print("=== 真类型 -> 被标成（最近邻≤2.0格，仅错位）top5 ===")
for (gt, ct), n in conf.most_common(10):
    print(f"{gt} -> {ct}: {n}")

# FP：没有 gold 最近邻≤1.5 的候选，按 tier/类型统计
matched_cand = set()
for gid, gt, ct, tier, d in pairs:
    pass
fp = Counter()
used = set()
for gid, gtype, gtile in G:
    best = None
    for i, c in enumerate(C):
        d = math.hypot(c["tile"][0] - gtile[0], c["tile"][1] - gtile[1])
        if best is None or d < best[0]:
            best = (d, i)
    if best and best[0] <= 1.5:
        used.add(best[1])
for i, c in enumerate(C):
    if i not in used:
        fp[c["type"]] += 1
print("=== FP 候选类型分布（未被 ≤1.5 格 gold 吸收）===")
for t, n in fp.most_common():
    print(f"{t}: {n}")

# 防空塔专项
ad = [b for b in gold["buildings"] if b["type"] == "air-defense"]
ad_hit = [p for p in pairs if p[1] == "air-defense"]
print(f"=== 防空：gold {len(ad)} 座；最近邻配对中标 air-defense 的 {sum(1 for p in pairs if p[2]=='air-defense')}；v2 全表 air-defense 标签 {sum(1 for c in C if c['type']=='air-defense')} ===")
