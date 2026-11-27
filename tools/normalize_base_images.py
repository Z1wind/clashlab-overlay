# -*- coding: utf-8 -*-
"""归一化：把 android/assets/img 里所有阵图按顺序重命名为 b01..bNN.jpg，确保 20 张且无重复。"""
import hashlib, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
D = os.path.join(BASE, "android", "assets", "img")
files = sorted(f for f in os.listdir(D) if f.lower().endswith(".jpg"))
print("files:", files)
seen = {}
keep = []
for f in files:
    p = os.path.join(D, f)
    h = hashlib.md5(open(p, "rb").read()).hexdigest()
    if h in seen:
        print("dup", f, "==", seen[h]); os.remove(p); continue
    seen[h] = f; keep.append(p)
print("unique:", len(keep))
# 先临时名，避免重命名冲突
tmp = []
for i, p in enumerate(keep, 1):
    t = os.path.join(D, "_tmp_%02d.jpg" % i)
    os.rename(p, t); tmp.append(t)
for i, t in enumerate(tmp, 1):
    os.rename(t, os.path.join(D, "b%02d.jpg" % i))
final = sorted(f for f in os.listdir(D) if f.lower().endswith(".jpg"))
print("final:", len(final), final)
