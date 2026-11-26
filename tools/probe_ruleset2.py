# -*- coding: utf-8 -*-
import glob, json, os, urllib.request
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
f = sorted(glob.glob(os.path.join(BASE, "out", "overlay", "_p3a", "upstream", "clash-of-clans-base-validator-main", "rulesets", "home-*.json")))[-1]
d = json.load(open(f, encoding="utf-8"))
print("ruleset:", os.path.basename(f), "| status:", d.get("review_status"), "| verified:", d.get("verified_on"))
objs = d.get("objects") or []
print("objects:", type(objs).__name__, len(objs) if hasattr(objs, "__len__") else "?")
if isinstance(objs, list) and objs:
    print("first object:", json.dumps(objs[0], ensure_ascii=False)[:600])
elif isinstance(objs, dict):
    k = list(objs)[0]
    print("first object key:", k, "->", json.dumps(objs[k], ensure_ascii=False)[:600])
ths = d.get("town_halls")
print("town_halls:", json.dumps(ths, ensure_ascii=False)[:900])
print("mergers:", json.dumps(d.get("mergers"), ensure_ascii=False)[:400])
# cocbases types
req = urllib.request.Request("https://cocbases.com/wp-json/wp/v2/types", headers={"User-Agent": "Mozilla/5.0 clashlab"})
with urllib.request.urlopen(req, timeout=40) as r:
    types = json.loads(r.read().decode("utf-8", "ignore"))
print("cocbases rest_bases:", [(k, v.get("rest_base")) for k, v in types.items()])
