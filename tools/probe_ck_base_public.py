# -*- coding: utf-8 -*-
import json, sys, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
doc = json.loads(urllib.request.urlopen(urllib.request.Request("https://api.clashk.ing/openapi.json",
    headers={"User-Agent": "clashlab"}), timeout=30).read().decode("utf-8", "ignore"))
paths = doc.get("paths") or {}
print("--- base/layout/war paths & security ---")
for p in sorted(paths):
    if any(k in p.lower() for k in ("base", "layout", "war", "army")):
        for m, op in (paths[p] or {}).items():
            print("%-52s %-5s security=%s" % (p, m.upper(), op.get("security")))
print("--- try public candidates ---")
def get(u):
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "clashlab"}), timeout=20) as r:
            return r.status, r.read().decode("utf-8", "ignore")[:260]
    except Exception as e:
        return "ERR", type(e).__name__ + ":" + str(e)[:80]
for u in ("https://api.clashk.ing/v2/bases/personal",
          "https://api.clashk.ing/v2/bases",
          "https://api.clashk.ing/v2/war/%2320R9PL0VU",
          "https://api.clashk.ing/v2/war/%2320R9PL0VU/layouts",
          "https://api.clashk.ing/v2/clan/%2320R9PL0VU/wars?limit=1",
          "https://api.clashk.ing/v2/clan/%2320R9PL0VU/cached"):
    print(u, "->", get(u))
