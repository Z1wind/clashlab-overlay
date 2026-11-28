# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
# 1) 训练：正样本中心 = 左上角 + 1.0（warp 中心 = 入参+0.5 → 入参用 x+0.5）
p = os.path.join(BASE, "tools", "train_hybrid_full.py")
t = open(p, encoding="utf-8").read()
t = t.replace('gpos.append((warp(b["img"], b["cal"], gx, gy), 1))',
              'gpos.append((warp(b["img"], b["cal"], gx + 0.5, gy + 0.5), 1))', 1)
t = t.replace('crops.append(warp(b["img"], b["cal"], gx, gy)); labels.append(TIDX[t])',
              'crops.append(warp(b["img"], b["cal"], gx + 0.5, gy + 0.5)); labels.append(TIDX[t])', 1)
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("train centered positives")
# 2) 推理：_crop(cx+.5, cy+.5) → 中心 cx+1.0（与训练一致）
q = os.path.join(BASE, "tools", "preannotate_core.py")
s = open(q, encoding="utf-8").read()
s = s.replace("_crop(img, cal, cx, cy, self.size)", "_crop(img, cal, cx + .5, cy + .5, self.size)")
open(q, "w", encoding="utf-8", newline="\n").write(s)
print("inference centered; count:", s.count("cx + .5, cy + .5"))
