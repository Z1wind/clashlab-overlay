# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "train_real_aug.py")
t = open(p, encoding="utf-8").read()
if "exclude-bases" not in t:
    t = t.replace('    ap.add_argument("--epochs", type=int, default=26)',
                  '    ap.add_argument("--epochs", type=int, default=26)\n    ap.add_argument("--exclude-bases", default="")', 1)
    t = t.replace("    items = []\n    for bi, base in enumerate(bases):",
                  "    excl = {int(x) for x in a.exclude_bases.split(',') if x.strip() != ''}\n    items = []\n    for bi, base in enumerate(bases):\n        if bi in excl: print('skip base', bi, flush=True); continue", 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("exclude-bases added")
else:
    print("already")
