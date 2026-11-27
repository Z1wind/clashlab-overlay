# -*- coding: utf-8 -*-
import json, os, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOKEN = os.environ["GH_TOKEN"]; API = "https://api.github.com"
def gh(u):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "clashlab", "Accept": "application/vnd.github+json"}
    with urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))
names = [it["name"] for it in gh(API + "/repos/ClashKingInc/ClashKingAssets/contents/assets")]
print("ClashKing assets dirs:", names)
for sub in ("troops", "spells", "pets", "icons", "heroes", "equipment"):
    if sub in names:
        try:
            items = gh(API + "/repos/ClashKingInc/ClashKingAssets/contents/assets/" + sub)
            print("==", sub, ":", len(items), "items; sample:", [it["name"] for it in items[:8]])
        except Exception as e:
            print("==", sub, "fail", str(e)[:80])
print("== Statscell troops/icons ==")
try:
    items = gh(API + "/repos/Statscell/clash-assets/contents/troops/icons")
    print(len(items), [it["name"] for it in items[:10]])
except Exception as e:
    print("fail", str(e)[:100])
