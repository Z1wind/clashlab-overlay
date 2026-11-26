# -*- coding: utf-8 -*-
import json, urllib.request
u = "https://api.clashk.ing/openapi.json"
req = urllib.request.Request(u, headers={"User-Agent": "clashlab"})
with urllib.request.urlopen(req, timeout=30) as r:
    raw = r.read()
doc = json.loads(raw.decode("utf-8", "ignore"))
print("openapi:", doc.get("openapi") or doc.get("swagger"), "| title:", (doc.get("info") or {}).get("title"))
paths = doc.get("paths") or {}
print("paths:", len(paths))
for p in sorted(paths)[:60]:
    methods = list((paths[p] or {}).keys())
    print("  ", p, methods)
print("security schemes:", list(((doc.get("components") or {}).get("securitySchemes") or {}).keys()))
json.dump({"paths": sorted(paths)}, open(r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\clashking_paths.json", "w", encoding="utf-8"), ensure_ascii=False)
