# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "train_hybrid_full.py")
t = open(p, encoding="utf-8").read()
t = t.replace('gpos.append((warp(b["img"], b["cal"], gx + 0.5, gy + 0.5), 1))',
              'gpos.append((warp(b["img"], b["cal"], gx, gy), 1))')
t = t.replace('crops.append(warp(b["img"], b["cal"], gx + 0.5, gy + 0.5)); labels.append(TIDX[t])',
              'crops.append(warp(b["img"], b["cal"], gx, gy)); labels.append(TIDX[t])')
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("train convention reverted")
