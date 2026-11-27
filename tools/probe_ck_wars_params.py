# -*- coding: utf-8 -*-
import json, os, sys, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
spec = json.load(open(os.path.join(BASE, "out", "api", "clashking_openapi.json"), encoding="utf-8"))
op = spec["paths"]["/v2/clan/{clanTag}/wars"]["get"]
print("wars params:")
for p in op.get("parameters") or []:
    print("  %-14s %-8s %s" % (p.get("name"), p.get("in"), (p.get("description") or "")[:70]))
print("cached params:")
op2 = spec["paths"]["/v2/clan/{tag}/cached"]["get"]
print(" security:", op2.get("security"), "| summary:", op2.get("summary"))
CK = "https://api.clashk.ing"
def get(u):
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "clashlab"}), timeout=30) as r:
            return r.status, r.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read(300).decode("utf-8", "ignore")
# 用我们之前抓到的真实战争部落 tag
res = os.path.join(BASE, "out", "live", "enemy_war_resolved.json")
tags = []
if os.path.exists(res):
    d = json.load(open(res, encoding="utf-8"))
    def walk(x):
        if isinstance(x, dict):
            if x.get("tag", "").startswith("#") and "clanLevel" in str(x) or ("tag" in x and "name" in x):
                tags.append(x["tag"])
            for v in x.values(): walk(v)
        elif isinstance(x, list):
            for v in x: walk(v)
    walk(d)
tags = list(dict.fromkeys(tags))[:3]
print("tags from capture:", tags)
for t in tags:
    q = urllib.parse.quote(t)
    for params in ("?limit=5", "?limit=5&page=1", "?limit=5&type=regular"):
        st, body = get(CK + "/v2/clan/%s/wars%s" % (q, params))
        try:
            j = json.loads(body); n = len(j.get("items") or [])
            first = (j.get("items") or [{}])[0]
            info = ("war keys=" + str(list(first.keys())[:8])) if isinstance(first, dict) and first else ""
        except Exception:
            n = "?"; info = body[:80]
        print("wars", t, params, "->", st, "items:", n, info)
# cached 完整字段
st, body = get(CK + "/v2/clan/%s/cached" % urllib.parse.quote("#PUP9P88R"))
j = json.loads(body)
print("cached full keys:", list(j.keys()))
for k in ("members", "memberList", "clanLevel", "warLeague", "capitalLeague"):
    v = j.get(k)
    print("  ", k, "->", (len(v) if isinstance(v, list) else (list(v.keys())[:6] if isinstance(v, dict) else v)))
