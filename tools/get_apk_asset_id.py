# -*- coding: utf-8 -*-
import json, os, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOKEN = os.environ["GH_TOKEN"]; REPO = "Z1wind/clashlab-overlay"; API = "https://api.github.com"
h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
with urllib.request.urlopen(urllib.request.Request(API + "/repos/%s/releases?per_page=10" % REPO, headers=h), timeout=60) as r:
    rels = json.loads(r.read().decode())
rel = next(x for x in rels if x["tag_name"] == "v0.3.0")
apk = next(a for a in rel["assets"] if a["name"] == "ClashLabAnnotator.apk")
print(apk["id"])
