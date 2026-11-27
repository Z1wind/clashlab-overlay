# -*- coding: utf-8 -*-
"""实测 api.clashk.ing 公开端点：状态码/类型/字段/是否要 token。"""
import json, sys, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = "https://api.clashk.ing"
TAG = "%23PLVYQ0G2U"
TAG2 = "%2320R9PL0VU"
EPS = [
    "/",
    "/v2/",
    "/docs",
    "/v2/player/search?query=Z1wind&limit=2",
    "/v2/clan/search?query=SHADOW&limit=2",
    "/v2/clan/" + TAG + "/wars",
    "/v2/player/" + TAG2 + "/war/attacks",
    "/v2/clan/" + TAG + "/members",
    "/v2/player/" + TAG2,
    "/v2/clan/" + TAG,
    "/v2/leaderboard/clans?limit=2",
    "/v2/bases/search?query=x",
    "/v2/server/1/bases",
]
def get(path):
    u = BASE + path
    req = urllib.request.Request(u, headers={"User-Agent": "clashlab-probe", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = r.read(1200).decode("utf-8", "ignore")
            return r.status, r.headers.get("Content-Type"), data
    except urllib.error.HTTPError as e:
        body = e.read(300).decode("utf-8", "ignore")
        return e.code, e.headers.get("Content-Type"), body
    except Exception as e:
        return "ERR", "", str(e)[:120]
for ep in EPS:
    st, ct, body = get(ep)
    keys = ""
    try:
        j = json.loads(body)
        keys = "keys=" + str(list(j.keys())[:6]) if isinstance(j, dict) else ("list[" + str(len(j)) + "]")
    except Exception:
        keys = body.replace("\n", " ")[:100]
    print("%-44s %-4s %-26s %s" % (ep[:44], st, (ct or "")[:26], keys[:150]))
