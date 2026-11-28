# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
t = open(os.path.join(BASE, "tools", "train_hybrid_cv.py"), encoding="utf-8").read()
old1 = 'for (t, gx, gy) in b["blds"]: gpos.append((warp(b["img"], b["cal"], gx, gy), 1))'
new1 = ('for (t, gx, gy) in b["blds"]:\n'
        '                gpos.append((warp(b["img"], b["cal"], gx, gy), 1)); gpos_types.append(t)')
if old1 not in t: print("anchor1 miss")
else: t = t.replace(old1, new1, 1)
if "gpos, gneg = [], [], []" not in t:
    t = t.replace("gpos, gneg = [], []", "gpos, gneg, gpos_types = [], [], []", 1)
old2 = "items = [(aug(c,rng),l) for (c,l) in [gpos[rng.randrange(len(gpos))] for _ in range(40)] + [gneg[rng.randrange(len(gneg))] for _ in range(40)]]"
new2 = ("_cnt = {}\n"
        "            for _t in gpos_types: _cnt[_t] = _cnt.get(_t, 0) + 1\n"
        "            _w = [1.0 / (_cnt[_t] ** 0.5) for _t in gpos_types]\n"
        "            _pick = rng.choices(gpos, weights=_w, k=40)\n"
        "            items = [(aug(c,rng),l) for (c,l) in _pick + [gneg[rng.randrange(len(gneg))] for _ in range(40)]]")
if old2 not in t: print("anchor2 miss")
else:
    t = t.replace(old2, new2, 1)
    t = t.replace('hybrid_report.json', 'hybrid_balgate_report.json')
    open(os.path.join(BASE, "tools", "train_hybrid_balgate_cv.py"), "w", encoding="utf-8", newline="\n").write(t)
    print("balanced gate CV written; gpos_types:", t.count("gpos_types"))
