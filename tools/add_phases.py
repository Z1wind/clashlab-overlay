# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "preannotate_core.py")
t = open(p, encoding="utf-8").read()
old = "    def detect(self, img, quad, gate_th=None, emb_th=None):"
new = "    def detect(self, img, quad, gate_th=None, emb_th=None, phases=(0.0,)):"
if old in t:
    t = t.replace(old, new, 1)
    old2 = "        cells = [(cx, cy) for cx in range(2, 42) for cy in range(2, 42)]\n        cands = []"
    new2 = "        cells = [(cx + off, cy + off) for off in phases for cx in range(2, 42) for cy in range(2, 42)]\n        cands = []"
    t = t.replace(old2, new2, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("phases support added")
else:
    print("anchor miss")
