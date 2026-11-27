# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "build_apk_ci.py")
t = open(p, encoding="utf-8").read()
old = '    ap.add_argument("--proj", default=env_dir("CLASHLAB_ANDROID") or os.path.join(ROOT, "android"))'
new = '''    _proj = env_dir("CLASHLAB_ANDROID")
    if not _proj:
        _cand = os.path.join(os.path.realpath(ROOT), "android")   # junction -> ASCII path
        _proj = _cand if os.path.isdir(_cand) else os.path.join(ROOT, "android")
    ap.add_argument("--proj", default=_proj)'''
if old in t:
    t = t.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("proj realpath patched")
else:
    print("anchor miss")
