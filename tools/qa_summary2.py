# -*- coding: utf-8 -*-
import json, os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
d = json.load(open(os.path.join(BASE, "out", "qa_e2e", "summary.json"), encoding="utf-8"))
for c in d["cases"]:
    print(json.dumps(c, ensure_ascii=False)[:700])
    print("---")
