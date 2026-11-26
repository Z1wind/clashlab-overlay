# -*- coding: utf-8 -*-
import json, urllib.request
def get(u):
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "clashlab"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.read().decode("utf-8", "ignore")
    except Exception as e:
        return "ERR", type(e).__name__ + ":" + str(e)[:60]
for u in ("https://api.clashk.ing/openapi.json", "https://api.clashk.ing/swagger.json",
          "https://api.clashk.ing/docs", "https://api.clashk.ing/api-docs",
          "https://api.clashk.ing/v1", "https://api.clashk.ing/player"):
    st, body = get(u)
    print(u, "->", st, "|", (body or "")[:160].replace("\n", " "))
