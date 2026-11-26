# -*- coding: utf-8 -*-
import json, urllib.request
req = urllib.request.Request("https://api.clashk.ing/openapi.json", headers={"User-Agent": "clashlab"})
raw = urllib.request.urlopen(req, timeout=30).read()
doc = json.loads(raw.decode("utf-8", "ignore"))
paths = doc.get("paths") or {}
sec = doc.get("components", {}).get("securitySchemes", {})
print("security schemes:", json.dumps(sec, ensure_ascii=False)[:500])
print("---- player/clan/war paths & security ----")
for p in sorted(paths):
    if any(k in p for k in ("player", "/war", "currentwar", "clan/{")) and "admin" not in p:
        for m, op in (paths[p] or {}).items():
            se = op.get("security")
            print("%-46s %-4s security=%s" % (p, m.upper(), se))
