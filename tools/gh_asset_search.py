# -*- coding: utf-8 -*-
import json, os, sys, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOKEN = os.environ["GH_TOKEN"]; API = "https://api.github.com"
def gh(u):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "clashlab", "Accept": "application/vnd.github+json"}
    with urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))
for q in ["clash of clans assets", "clash of clans icons", "clashking assets", "coc troops png"]:
    print("=== " + q + " ===")
    try:
        for it in gh(API + "/search/repositories?" + urllib.parse.urlencode(
                {"q": q, "sort": "stars", "order": "desc", "per_page": 6})).get("items") or []:
            print("%5d %-40s %-10s %s" % (it["stargazers_count"], (it["full_name"] or "")[:40],
                  (it.get("language") or "-")[:10], (it.get("description") or "")[:60]))
    except Exception as e:
        print("fail:", str(e)[:100])
