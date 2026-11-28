# -*- coding: utf-8 -*-
"""类别平衡门控：稀有类型正样本更高采样权重。"""
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
t = open(os.path.join(BASE, "tools", "train_hybrid_cv.py"), encoding="utf-8").read()
old1 = 'for (t, gx, gy) in b["blds"]: gpos.append((warp(b["img"], b["cal"], gx, gy), 1))'
new1 = ('for (t, gx, gy) in b["blds"]:\n'
        '                gpos.append((warp(b["img"], b["cal"], gx, gy), 1)); gpos_types.append(t)')
if old1 in t:
    t = t.replace(old1, new1, 1)
else:
    print("anchor1 miss"); raise SystemExit(1)
# 初始化 gpos_types
t = t.replace("        gpos, gneg = [], []", "        gpos, gneg, gpos_types = [], [], []", 1)
# 加权采样
old2 = 'items = [gpos[rng.randrange(len(gpos))] for _ in range(40)] + [gneg[rng.randrange(len(gneg))] for _ in range(40)]'
new2 = ('_cnt = {}\n'
        '            for _t in gpos_types: _cnt[_t] = _cnt.get(_t, 0) + 1\n'
        '            _w = [1.0 / (_cnt[_t] ** 0.5) for _t in gpos_types]\n'
        '            items = rng.choices(gpos, weights=_w, k=40) + [gneg[rng.randrange(len(gneg))] for _ in range(40)]')
if old2 in t:
    t = t.replace(old2, new2, 1)
    t = t.replace('hybrid_report.json', 'hybrid_balgate_report.json')
    open(os.path.join(BASE, "tools", "train_hybrid_balgate_cv.py"), "w", encoding="utf-8", newline="\n").write(t)
    print("balanced gate CV written")
else:
    print("anchor2 miss")
