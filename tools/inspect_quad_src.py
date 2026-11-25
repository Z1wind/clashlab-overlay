# -*- coding: utf-8 -*-
import os, json
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
for b in ("03", "05", "06"):
    p = os.path.join(BASE, "bases", "th16", b, "layout.json")
    d = json.load(open(p, encoding="utf-8"))
    print(b, "keys:", list(d.keys())[:10])
q = os.path.join(BASE, "out", "overlay", "_quad_calib", "summary.json")
print("quad_calib exists:", os.path.exists(q))
if os.path.exists(q):
    s = json.load(open(q, encoding="utf-8"))
    print("type", type(s), "keys:", list(s.keys())[:8] if isinstance(s, dict) else len(s))
    txt = json.dumps(s, ensure_ascii=False)
    print(txt[:500])
