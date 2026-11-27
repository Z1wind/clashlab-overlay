# -*- coding: utf-8 -*-
import json, os, sys, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOKEN = os.environ["GH_TOKEN"]; API = "https://api.github.com"
def gh(u):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "clashlab", "Accept": "application/vnd.github+json"}
    with urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))
for repo in ("ClashKingInc/ClashKingAssets", "Statscell/clash-assets"):
    print("=== " + repo + " ===")
    try:
        d = gh(API + "/repos/%s/contents/" % repo)
        for it in d[:25]:
            print(" %-8s %-40s %s" % (it["type"], it["name"], it.get("size") or ""))
    except Exception as e:
        print("fail:", str(e)[:150])
