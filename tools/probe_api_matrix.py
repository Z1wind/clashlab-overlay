# -*- coding: utf-8 -*-
import json, sys, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CK = "https://api.clashk.ing"
def get(url, timeout=25):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "clashlab"}), timeout=timeout) as r:
            return r.status, r.read(5000).decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read(400).decode("utf-8", "ignore")
    except Exception as e:
        return "ERR", str(e)[:130]
# 1) 动态静态数据（正确显示名）
for name in ("Electro Dragon", "Town Hall", "Balloon"):
    for cat in ("troops", "buildings"):
        u = CK + "/v2/static/%s/%s/max-level" % (cat, urllib.parse.quote(name))
        st, body = get(u)
        if st == 200:
            print("max-level", cat, name, "->", body[:100]); break
# 2) 玩家搜索结果字段（是否含 TH）
st, body = get(CK + "/v2/player/search?query=Z1wind&limit=1")
j = json.loads(body); it = (j.get("items") or [{}])[0]
print("player search keys:", list(it.keys())[:14])
print("  sample:", {k: it.get(k) for k in ("name","tag","townHallLevel","clan") if k in it})
# 3) 多个 clan 的 wars（找有数据的）
st, body = get(CK + "/v2/clan/search?query=SHADOW&limit=3")
tags = [x["tag"] for x in json.loads(body).get("items") or []]
print("clan search tags:", tags)
for t in tags:
    st, body = get(CK + "/v2/clan/%s/wars?limit=2" % urllib.parse.quote(t))
    try:
        n = len(json.loads(body).get("items") or [])
    except Exception:
        n = "?"
    print("wars", t, "->", st, "items:", n)
# 4) 官方 API 无 token/白名单
st, body = get("https://api.clashofclans.com/v1/clans/%23PLVYQ0G2U", timeout=20)
print("official API ->", st, body[:160])
# 5) ClashKing bases（需 token）
st, body = get(CK + "/v2/server/1/bases")
print("server bases ->", st, body[:140])
