# -*- coding: utf-8 -*-
import os, json, hashlib
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
P3A = os.path.join(BASE, "out", "overlay", "_p3a")
rep = os.path.join(P3A, "report.md")
if os.path.exists(rep):
    b = open(rep, "rb").read()
    print("report.md", len(b), "B md5", hashlib.md5(b).hexdigest().upper()[:16])
# compare.json
for fn in ("compare.json", "summary.json"):
    p = os.path.join(P3A, "converted", fn)
    if os.path.exists(p):
        d = json.load(open(p, encoding="utf-8"))
        print(fn, "type", type(d).__name__, "keys", list(d.keys())[:10] if isinstance(d, dict) else len(d))
        s = json.dumps(d, ensure_ascii=False)
        print("  head:", s[:600])
