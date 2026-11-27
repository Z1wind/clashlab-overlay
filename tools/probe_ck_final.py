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
    except Exception as e:
        return "ERR", str(e)[:120]
def brief(body):
    try:
        j = json.loads(body)
        if isinstance(j, dict):
            if "items" in j:
                return "items=%d" % len(j["items"] or [])
            return "keys=" + str(list(j.keys())[:8])
        return "list=%d" % len(j)
    except Exception:
        return body[:80].replace("\n", " ")
tag = "#PLVYQ0G2U"
for enc in (urllib.parse.quote(tag), urllib.parse.quote(tag, safe=""), tag.replace("#", "")):
    st, body = get(CK + "/v2/clan/%s/wars?limit=2" % enc)
    print("wars enc=%-24s -> %s %s" % (enc, st, brief(body)))
for t in ("#PUP9P88R", "#YCPGVQYG", "#20PJQ0Y2R"):
    st, body = get(CK + "/v2/clan/%s/cached" % urllib.parse.quote(t))
    print("cached", t, "->", st, brief(body))
st, body = get(CK + "/v2/player/%s/battlelog/history" % urllib.parse.quote("#QCRJPL2RJ"))
print("battlelog ->", st, brief(body))
st, body = get(CK + "/v2/player/%s/activity-summary" % urllib.parse.quote("#QCRJPL2RJ"))
print("activity ->", st, brief(body))
