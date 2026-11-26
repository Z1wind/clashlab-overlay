# -*- coding: utf-8 -*-
import json, os, urllib.request, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOKEN = os.environ["GH_TOKEN"]; REPO = "Z1wind/clashlab-overlay"; API = "https://api.github.com"
def get(u):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
    with urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))
rels = get(API + "/repos/%s/releases?per_page=10" % REPO)
rel = next((x for x in rels if x["tag_name"] == "backup-2026-11-26"), None)
print("release:", rel["id"], rel["tag_name"], "prerelease=", rel["prerelease"])
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
local = {"ClashOverlay.exe": os.path.getsize(os.path.join(BASE, "dist", "ClashOverlay.exe")),
         "clashlab_annotated_20261126.zip": os.path.getsize(os.path.join(BASE, "out", "backup", "clashlab_annotated_20261126.zip"))}
for a in rel["assets"]:
    print("ASSET", a["name"], "size=", a["size"], "state=", a["state"], "local_match=", a["size"] == local.get(a["name"]))
    print("  url:", a["browser_download_url"])
print("source zip:", rel.get("zipball_url"))
