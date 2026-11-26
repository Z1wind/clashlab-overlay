# -*- coding: utf-8 -*-
import json, os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
d = json.load(open(os.path.join(BASE, "out", "qa_e2e", "summary.json"), encoding="utf-8"))
cases = d.get("cases") or d.get("results") or []
print("keys:", list(d.keys()))
for c in cases:
    print(c.get("name") or c.get("tag"), "->", c.get("status") or c.get("ok"), "|", str(c.get("detail") or c.get("reason") or "")[:160])
