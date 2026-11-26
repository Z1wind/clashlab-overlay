# -*- coding: utf-8 -*-
import json, urllib.parse, urllib.request
TAG = "QCRJPL2RJ"
def get(u):
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "clashlab", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, r.read().decode("utf-8", "ignore")
    except Exception as e:
        return "ERR", type(e).__name__ + ":" + str(e)[:80]
enc = urllib.parse.quote("#" + TAG)
cands = [
    "https://api.clashk.ing/v2/player/%s/history/stats" % enc,
    "https://api.clashk.ing/v2/player/%s/war/stats" % enc,
    "https://api.clashk.ing/v2/player/%s/war/attacks" % enc,
    "https://api.clashk.ing/v2/player/%s/current" % enc,
    "https://api.clashk.ing/player/%s/warhits" % enc,
    "https://api.clashk.ing/v2/player/search?tag=%s" % urllib.parse.quote("QCRJPL2RJ"),
    "https://api.clashk.ing/v2/player/search?playerTag=%s" % enc,
]
for u in cands:
    st, body = get(u)
    print(u, "->", st, "|", (body or "")[:220].replace("\n", " "))
