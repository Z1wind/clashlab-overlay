# -*- coding: utf-8 -*-
import json, os, urllib.request
TOKEN = os.environ["GH_TOKEN"]
def api(u):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "clashlab", "Accept": "application/vnd.github+json"}
    with urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))
def probe(u):
    try:
        req = urllib.request.Request(u, method="HEAD", headers={"User-Agent": "clashlab"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return "%s %s %s" % (r.status, r.headers.get("content-length"), r.headers.get("content-type"))
    except Exception as e:
        return "ERR " + type(e).__name__ + ":" + str(e)[:60]

U, R = "ClashKingInc", "ClashKingAssets"
for path in ("assets", "assets/buildings", "assets/troops", "assets/heroes", "artwork", "internal"):
    try:
        items = api("https://api.github.com/repos/%s/%s/contents/%s" % (U, R, path))
        names = [(i["type"], i["name"]) for i in items][:25]
        print("==", path, "->", len(items), "entries")
        print("  ", names)
    except Exception as e:
        print("==", path, "ERR", str(e)[:80])

print("---- CDN probe ----")
for u in ("https://assets.clashk.ing/troops/barbarian/icon.webp",
          "https://assets.clashk.ing/",
          "https://raw.githubusercontent.com/ClashKingInc/ClashKingAssets/main/README.md"):
    print(u, "->", probe(u))
