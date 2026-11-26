# -*- coding: utf-8 -*-
import json, urllib.parse, urllib.request
def get(u):
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "clashlab", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.read().decode("utf-8", "ignore")[:400]
    except Exception as e:
        return "ERR", type(e).__name__ + ":" + str(e)[:90]
# openapi 参数
doc = json.loads(urllib.request.urlopen(urllib.request.Request("https://api.clashk.ing/openapi.json",
    headers={"User-Agent": "c"}), timeout=30).read().decode("utf-8", "ignore"))
for p in ("/v2/player/search", "/v2/clan/search"):
    op = (doc["paths"].get(p) or {}).get("get") or {}
    print(p, "params:", [(x.get("name"), x.get("in"), x.get("required"), (x.get("schema") or {}).get("type")) for x in op.get("parameters", [])])
print("---- try search variants ----")
for u in ("https://api.clashk.ing/v2/player/search?name=z1wind&limit=3",
          "https://api.clashk.ing/v2/player/search?query=z1wind",
          "https://api.clashk.ing/v2/clan/search?name=ClashKing&limit=3",
          "https://api.clashk.ing/v2/clan/search?query=ClashKing"):
    print(u, "->", get(u))
