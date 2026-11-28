# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "train_real_aug.py")
t = open(p, encoding="utf-8").read()
if "add_argument(\"--size\"" not in t:
    t = t.replace('    ap.add_argument("--exclude-bases", default="")',
                  '    ap.add_argument("--exclude-bases", default="")\n    ap.add_argument("--size", type=int, default=112)', 1)
    t = t.replace("    S = 112\n", "    S = int(a.size)\n", 1) if "    S = 112\n" in t else t
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("size arg added")
else:
    print("already")
