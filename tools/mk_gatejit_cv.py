# -*- coding: utf-8 -*-
"""门控正样本抖动增强 CV：正样本中心随机 ±0.75 格，提升密集/偏移下的召回。"""
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
t = open(os.path.join(BASE, "tools", "train_hybrid_cv.py"), encoding="utf-8").read()
old = 'for (t, gx, gy) in b["blds"]: gpos.append((warp(b["img"], b["cal"], gx, gy), 1))'
new = ('for (t, gx, gy) in b["blds"]:\n'
       '                for _ in range(3):\n'
       '                    jx = gx + rng.uniform(-0.75, 0.75); jy = gy + rng.uniform(-0.75, 0.75)\n'
       '                    gpos.append((warp(b["img"], b["cal"], jx, jy), 1))')
if old in t:
    t = t.replace(old, new, 1)
    t = t.replace('hybrid_report.json', 'hybrid_gatejit_report.json')
    open(os.path.join(BASE, "tools", "train_hybrid_gatejit_cv.py"), "w", encoding="utf-8", newline="\n").write(t)
    print("gate-jitter CV written")
else:
    print("anchor miss")
