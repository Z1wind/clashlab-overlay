# -*- coding: utf-8 -*-
import json, os
p = os.path.join(r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat", "models", "metrics.json")
d = json.load(open(p, encoding="utf-8"))
print(json.dumps(d, ensure_ascii=False)[:1800])
