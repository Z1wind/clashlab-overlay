# -*- coding: utf-8 -*-
"""诊断：67 条标注里有多少是「同一栋建筑在不同块里被重复标注」。
方法：各标注点裁 300px → 108px，两两做归一化互相关；同建筑重叠块的裁剪应高度相似。
"""
import json, os
from collections import Counter, defaultdict
import numpy as np, cv2
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
HI = os.path.join(BASE, "out", "overlay", "_auto_label", "hi")
MAX = os.path.join(BASE, "out", "overlay", "_recon", "max")
rows = []
for fn in ("labels_max.json", "labels_max2.json", "labels_max3.json", "labels_max4.json"):
    p = os.path.join(HI, fn)
    if os.path.exists(p):
        rows += json.load(open(p, encoding="utf-8"))
imgs, feats = {}, []
for r in rows:
    b = r["block"]
    if b not in imgs:
        imgs[b] = cv2.imdecode(np.fromfile(os.path.join(MAX, b + ".png"), np.uint8), cv2.IMREAD_COLOR)
    img = imgs[b]
    half = 150
    x0 = max(0, min(r["x"] - half, img.shape[1] - 300))
    y0 = max(0, min(r["y"] - half, img.shape[0] - 300))
    c = cv2.resize(img[y0:y0 + 300, x0:x0 + 300], (108, 108), interpolation=cv2.INTER_AREA)
    g = cv2.cvtColor(c, cv2.COLOR_BGR2GRAY).astype(np.float32)
    g = (g - g.mean()) / (g.std() + 1e-6)
    feats.append(g.ravel())
F = np.stack(feats)
S = (F @ F.T) / F.shape[1]
np.fill_diagonal(S, -9)
n = len(rows)
# 贪心聚类：相似度 > 0.86 视为同一栋（跨块重复）
parent = list(range(n))
def find(a):
    while parent[a] != a:
        parent[a] = parent[parent[a]]; a = parent[a]
    return a
def union(a, b):
    ra, rb = find(a), find(b)
    if ra != rb:
        parent[ra] = rb
for i in range(n):
    for j in range(i + 1, n):
        if S[i, j] > 0.86:
            union(i, j)
groups = defaultdict(list)
for i in range(n):
    groups[find(i)].append(i)
dups = [g for g in groups.values() if len(g) > 1]
print("labels=%d unique_groups=%d dup_groups=%d" % (n, len(groups), len(dups)))
for g in sorted(dups, key=lambda x: -len(x)):
    types = Counter(rows[i]["type"] for i in g)
    print("  group size=%d types=%s blocks=%s" % (len(g), dict(types), sorted(set(rows[i]["block"] for i in g))))
print("类内唯一数：")
rows_by_type = Counter(rows[i]["type"] for i in range(n))
uniq_by_type = Counter()
for root_i, g in groups.items():
    t = Counter(rows[i]["type"] for i in g).most_common(1)[0][0]
    uniq_by_type[t] += 1
for t in sorted(rows_by_type):
    print("  %-20s labels=%-2d unique=%d" % (t, rows_by_type[t], uniq_by_type[t]))
res = {"labels": n, "unique": len(groups), "dup_groups": len(dups),
       "by_type": {t: {"labels": rows_by_type[t], "unique": uniq_by_type[t]} for t in sorted(rows_by_type)}}
json.dump(res, open(os.path.join(HI, "dup_report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
