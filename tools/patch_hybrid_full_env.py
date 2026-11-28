# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
# 1) train_hybrid_full 支持 CLASHLAB_EXPORTS
p = os.path.join(BASE, "tools", "train_hybrid_full.py")
t = open(p, encoding="utf-8").read()
old = '''    paths = [os.path.join(os.path.expanduser("~"), "Downloads", "annot_b01 (1).json"),
             os.path.join(os.path.expanduser("~"), "Downloads", "annot_b02 (1).json")]
    paths += [os.path.join(os.path.expanduser("~"), "Downloads", "annot_b%02d.json" % i) for i in range(3, 9)]'''
new = '''    env = os.environ.get("CLASHLAB_EXPORTS", "")
    if env:
        paths = [x for x in env.split(";") if x.strip()]
    else:
        paths = [os.path.join(os.path.expanduser("~"), "Downloads", "annot_b01 (1).json"),
                 os.path.join(os.path.expanduser("~"), "Downloads", "annot_b02 (1).json")]
        paths += [os.path.join(os.path.expanduser("~"), "Downloads", "annot_b%02d.json" % i) for i in range(3, 9)]'''
if old in t:
    t = t.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("train_hybrid_full env-aware")
else:
    print("anchor miss")
