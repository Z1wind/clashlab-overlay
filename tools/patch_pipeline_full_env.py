# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "train_pipeline_full.py")
t = open(p, encoding="utf-8").read()
old = 'paths = [os.path.join(os.path.expanduser("~"), "Downloads", "annot_b%02d.json" % i) for i in range(1, 9)]'
new = 'env = os.environ.get("CLASHLAB_EXPORTS", "")\nif env:\n    paths = [x for x in env.split(";") if x.strip()]\nelse:\n    paths = [os.path.join(os.path.expanduser("~"), "Downloads", "annot_b%02d.json" % i) for i in range(1, 9)]'
if old in t:
    t = t.replace(old, new, 1)
    t = t.replace('    if bi in (0, 1): continue\n', '    if "CLASHLAB_KEEP_BAD" not in os.environ and bi in (0, 1) and not env: continue\n')
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("pipeline_full paths patched")
else:
    print("anchor miss")
