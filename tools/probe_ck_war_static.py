# -*- coding: utf-8 -*-
import json, sys, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = "https://api.clashk.ing"
CLAN = urllib.parse.quote("#PLVYQ0G2U")
def get(path):
    try:
        with urllib.request.urlopen(urllib.request.Request(BASE + path, headers={"User-Agent": "clashlab"}), timeout=25) as r:
            return r.status, r.read(6000).decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read(300).decode("utf-8", "ignore")
    except Exception as e:
        return "ERR", str(e)[:120]
# 1) wars 真实结构：找成员与 TH
st, body = get("/v2/clan/%s/wars?limit=1" % CLAN)
print("wars status:", st)
try:
    j = json.loads(body)
    it = (j.get("items") or [])[0]
    print("war top keys:", list(it.keys())[:14])
    for k in ("clan", "opponent", "members", "attacks", "teamSize", "state", "polling"):
        if k in it:
            v = it[k]
            print(" ", k, type(v).__name__, (len(v) if isinstance(v, list) else (list(v.keys())[:10] if isinstance(v, dict) else v)))
    mem = it.get("clan", {}).get("members") if isinstance(it.get("clan"), dict) else None
    if mem:
        m0 = mem[0]
        print("  member sample keys:", list(m0.keys()))
        print("  member sample:", {k: m0.get(k) for k in ("tag", "name", "townHallLevel", "mapPosition")})
except Exception as e:
    print("parse err:", e, body[:120])
# 2) 静态数据端点
for cat in ("troops", "buildings", "spells", "heroes", "pets", "equipment", "townhalls"):
    st, body = get("/v2/static/%s/names" % cat)
    print("static names %-10s -> %s %s" % (cat, st, body[:110]))
for path in ("/v2/static/troops/edrag/max-level", "/v2/static/buildings/town_hall/max-level",
             "/v2/static/troops/names?townhall=16"):
    st, body = get(path)
    print("%-52s -> %s %s" % (path, st, body[:120]))
