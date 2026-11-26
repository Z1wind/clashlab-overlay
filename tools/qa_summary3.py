# -*- coding: utf-8 -*-
import json, os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
d = json.load(open(os.path.join(BASE, "out", "qa_e2e", "summary.json"), encoding="utf-8"))
c = d["cases"][0]
print("case keys:", list(c.keys()))
for cc in d["cases"]:
    print(cc["id"], "| keys:", {k: cc[k] for k in cc if k not in ("key_lines", "shots")})
