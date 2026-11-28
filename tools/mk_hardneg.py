# -*- coding: utf-8 -*-
"""硬负样本门控：负样本 50% 取建筑周围 2.2-4.5 格的环带（墙/装饰）。"""
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
t = open(os.path.join(BASE, "tools", "train_hybrid_cv.py"), encoding="utf-8").read()
old = '''            while tries < 8000 and len(gneg) < 110*len(tr):
                tries += 1
                cx = rng.uniform(1.5,42.5); cy = rng.uniform(1.5,42.5)
                if any(abs(cx-(gx+.5))+abs(cy-(gy+.5)) < 2.2 for (_,gx,gy) in b["blds"]): continue
                gneg.append((warp(b["img"], b["cal"], cx, cy), 0))'''
new = '''            while tries < 12000 and len(gneg) < 110*len(tr):
                tries += 1
                cx = rng.uniform(1.5,42.5); cy = rng.uniform(1.5,42.5)
                dists = [abs(cx-(gx+.5))+abs(cy-(gy+.5)) for (_,gx,gy) in b["blds"]]
                if not dists: continue
                dm = min(dists)
                if dm < 2.2: continue
                if rng.random() < 0.5 and dm > 4.5: continue
                gneg.append((warp(b["img"], b["cal"], cx, cy), 0))'''
if old in t:
    t = t.replace(old, new, 1)
    t = t.replace('hybrid_report.json', 'hybrid_hardneg_report.json')
    open(os.path.join(BASE, "tools", "train_hybrid_hardneg_cv.py"), "w", encoding="utf-8", newline="\n").write(t)
    print("hardneg script written")
else:
    print("anchor miss")
