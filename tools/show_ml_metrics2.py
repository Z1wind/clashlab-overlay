# -*- coding: utf-8 -*-
import json, os
p = os.path.join(r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat", "models", "metrics.json")
d = json.load(open(p, encoding="utf-8"))
for k in ("within_5fold", "lobo", "majority", "notes"):
    v = d.get(k)
    if isinstance(v, dict):
        print(k, "->", {kk: v[kk] for kk in v if kk not in ("per_fold", "per_base", "confusion")})
    else:
        print(k, "->", v)
