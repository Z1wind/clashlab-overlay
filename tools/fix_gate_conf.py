# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "auto_candidates.py")
t = open(p, encoding="utf-8").read()
t = t.replace('items.append({"tile": [x, y], "size": size, "gate_conf": round(float(prob), 4)})',
              'items.append({"tile": [x, y], "size": size, "gate_conf": round(float(prob), 4),\n                              "conf": round(float(prob), 4)})')
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("conf added for gate-only")
