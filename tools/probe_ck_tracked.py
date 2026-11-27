# -*- coding: utf-8 -*-
import json, sys, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CK = "https://api.clashk.ing"
def get(u):
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "clashlab"}), timeout=30) as r:
            return r.status, r.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read(300).decode("utf-8", "ignore")
st, body = get(CK + "/v2/clan/%s/cached" % urllib.parse.quote("#PUP9P88R"))
j = json.loads(body)
mem = j.get("members") or []
print("cached member sample:", json.dumps(mem[0], ensure_ascii=False)[:300] if mem else None)
print("member keys:", list(mem[0].keys()) if mem else None)
# 试 wars 带时间过滤
for q in ("?limit=10&time[after]=2026-01-01", "?limit=10&time[after]=2026-01-01T00:00:00Z", "?limit=10&type=cwl"):
    st, body = get(CK + "/v2/clan/%s/wars%s" % (urllib.parse.quote("#PUP9P88R"), q))
    try:
        n = len(json.loads(body).get("items") or [])
    except Exception:
        n = "?"
    print("wars", q, "->", st, "items:", n)
# 找大部落（搜索）再试 wars
st, body = get(CK + "/v2/clan/search?query=Clash%20of%20Clans&limit=3")
items = json.loads(body).get("items") or []
for it in items:
    t = it["tag"]
    st2, b2 = get(CK + "/v2/clan/%s/wars?limit=2" % urllib.parse.quote(t))
    try:
        n2 = len(json.loads(b2).get("items") or [])
    except Exception:
        n2 = "?"
    print("big clan", it.get("name"), t, "members:", it.get("members"), "wars items:", st2, n2)
