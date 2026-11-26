# -*- coding: utf-8 -*-
import json, urllib.parse, urllib.request
TAG = "QCRJPL2RJ"
def get(u):
    req = urllib.request.Request(u, headers={"User-Agent": "clashlab", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))
enc = urllib.parse.quote("#" + TAG)
d = get("https://api.clashk.ing/player/%s/warhits" % enc)
print("items:", len(d.get("items") or []))
it = (d.get("items") or [{}])[0]
print("item keys:", list(it.keys()))
wd = it.get("war_data") or {}
print("war_data keys:", list(wd.keys())[:30])
for side in ("clan", "opponent"):
    c = wd.get(side) or {}
    print("--", side, "keys:", list(c.keys())[:12])
    mem = (c.get("members") or [])[:2]
    print("   member keys:", list((mem[0] or {}).keys()) if mem else "none")
    if mem:
        print("   member sample:", json.dumps(mem[0], ensure_ascii=False)[:500])
hits = it.get("hits") or []
print("hits:", len(hits), "keys:", list((hits[0] or {}).keys()) if hits else "[]")
if hits:
    print("hit sample:", json.dumps(hits[0], ensure_ascii=False)[:700])
