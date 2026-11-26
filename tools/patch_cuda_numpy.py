# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "train_synth_level.py")
t = open(p, encoding="utf-8").read()
if "detach().cpu()" in t:
    print("already patched")
else:
    t = t.replace("                pred_lv = lv.numpy() * mx[val]", "                pred_lv = lv.detach().cpu().numpy() * mx[val]")
    t = t.replace("        pred_lv = lv.numpy() * mx[val]", "        pred_lv = lv.detach().cpu().numpy() * mx[val]")
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("cuda numpy fix applied")
