# -*- coding: utf-8 -*-
import json, urllib.parse, urllib.request
req = urllib.request.Request("https://api.clashk.ing/openapi.json", headers={"User-Agent": "clashlab"})
doc = json.loads(urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore"))
paths = doc.get("paths") or {}
print("---- /v2/player paths ----")
for p in sorted(paths):
    if p.startswith("/v2/player") and any(k in p for k in ("profile", "stats", "search", "current", "war")):
        print(" ", p, list(paths[p].keys()))
def get(u):
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "clashlab"}), timeout=20)
        return r.status, r.read().decode("utf-8", "ignore")[:400]
    except Exception as e:
        return "ERR", type(e).__name__ + ":" + str(e)[:80]
for u in ("https://api.clashk.ing/v2/player/search?name=ClashKing",
          "https://api.clashk.ing/v2/player/search?name=%23",
          "https://api.clashk.ing/v2/player/%232PP/current" ):
    print(u, "->", get(u))
