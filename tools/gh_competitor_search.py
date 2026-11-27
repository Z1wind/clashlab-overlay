# -*- coding: utf-8 -*-
import json, os, sys, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOKEN = os.environ["GH_TOKEN"]; API = "https://api.github.com"
QUERIES = ["clash of clans overlay", "clash of clans analyzer", "clash of clans api client",
           "clash of clans layout", "clash of clans bot", "clash of clans scouting"]
def search(q, n=8):
    u = API + "/search/repositories?" + urllib.parse.urlencode({"q": q, "sort": "stars", "order": "desc", "per_page": n})
    h = {"Authorization": "token " + TOKEN, "User-Agent": "clashlab", "Accept": "application/vnd.github+json"}
    with urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "ignore")).get("items") or []
for q in QUERIES:
    print("=== " + q + " ===")
    for it in search(q):
        print("%5d  %-40s %-26s %s" % (it["stargazers_count"], (it["full_name"] or "")[:40], (it.get("language") or "-")[:26], (it.get("description") or "")[:70]))
