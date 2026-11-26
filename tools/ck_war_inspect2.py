# -*- coding: utf-8 -*-
import json, urllib.parse, urllib.request
TAG = "QCRJPL2RJ"; CLAN = "2GYU8JRPV"
def get(u):
    req = urllib.request.Request(u, headers={"User-Agent": "clashlab", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))
enc = urllib.parse.quote("#" + TAG)
d = get("https://api.clashk.ing/v2/player/%s/war/attacks" % enc)
print("attacks items:", len(d.get("items") or []))
if d.get("items"):
    print("first keys:", list(d["items"][0].keys()))
    print(json.dumps(d["items"][0], ensure_ascii=False)[:900])
c = get("https://api.clashk.ing/v2/clan/%s/wars" % urllib.parse.quote("#" + CLAN))
print("clan wars items:", len(c.get("items") or []))
if c.get("items"):
    it = c["items"][0]
    print("war keys:", list(it.keys())[:25])
    for side in ("clan", "opponent"):
        m = (it.get(side) or {}).get("members") or []
        print(side, "members:", len(m), "| keys:", list(m[0].keys())[:25] if m else "-")
        if m:
            print("  sample:", json.dumps(m[0], ensure_ascii=False)[:400])
