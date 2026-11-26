# -*- coding: utf-8 -*-
import json, os
p = os.path.join(r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat", "out", "qa_e2e", "summary.json")
if os.path.exists(p):
    d = json.load(open(p, encoding="utf-8"))
    print(json.dumps(d, ensure_ascii=False, indent=1)[:2500])
else:
    print("missing")
