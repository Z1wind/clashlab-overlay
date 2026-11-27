# -*- coding: utf-8 -*-
import json, os, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOKEN = os.environ["GH_TOKEN"]; API = "https://api.github.com"
def gh(u):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "clashlab", "Accept": "application/vnd.github+json"}
    with urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))
def ls(repo, path):
    print("==", repo, path)
    try:
        for it in gh(API + "/repos/%s/contents/%s" % (repo, path))[:20]:
            print(" %-6s %-38s %s" % (it["type"], it["name"], it.get("size") or ""))
    except Exception as e:
        print(" fail:", str(e)[:120])
ls("Statscell/clash-assets", "troops")
ls("ClashKingInc/ClashKingAssets", "assets")
ls("ClashKingInc/ClashKingAssets", "artwork")
