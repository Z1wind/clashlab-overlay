# -*- coding: utf-8 -*-
import json, os, sys, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOKEN = os.environ["GH_TOKEN"]; API = "https://api.github.com"
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
def gh(u):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "clashlab", "Accept": "application/vnd.github+json"}
    with urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))
for q in ["clash of clans data json", "clash of clans static data", "clash of clans api proxy"]:
    print("=== " + q + " ===")
    u = API + "/search/repositories?" + urllib.parse.urlencode({"q": q, "sort": "stars", "order": "desc", "per_page": 6})
    try:
        for it in gh(u).get("items") or []:
            print("%5d %-42s %-10s %s" % (it["stargazers_count"], (it["full_name"] or "")[:42],
                  (it.get("language") or "-")[:10], (it.get("description") or "")[:60]))
    except Exception as e:
        print("search fail:", str(e)[:100])

# 扫 openapi 里的静态数据/资源类端点
spec = json.load(open(os.path.join(BASE, "out", "api", "clashking_openapi.json"), encoding="utf-8"))
paths = spec.get("paths") or {}
print("\n=== openapi 中 static/asset/troop/building 相关 ===")
for p, item in paths.items():
    if any(k in p.lower() for k in ("static", "asset", "troop", "building", "json", "locale")):
        for m, op in item.items():
            if m in ("get", "post"):
                print("%-60s %-4s %s" % (p[:60], m.upper(), (op.get("summary") or "")[:60]))
