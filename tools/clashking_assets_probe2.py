# -*- coding: utf-8 -*-
import json, os, urllib.request
TOKEN = os.environ["GH_TOKEN"]
def api(u):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "clashlab", "Accept": "application/vnd.github+json"}
    with urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))
U, R = "ClashKingInc", "ClashKingAssets"
def ls(path, show=40):
    try:
        items = api("https://api.github.com/repos/%s/%s/contents/%s" % (U, R, path))
        print("==", path, "->", len(items), "entries")
        print("  ", [(i["type"][0], i["name"]) for i in items][:show])
    except Exception as e:
        print("==", path, "ERR", str(e)[:90])
ls("assets/buildings/home-village")
ls("assets/buildings/home-village/cannon")
ls("assets/troops/giant")
ls("assets/landscape", 20)
ls("assets/equipment", 20)
