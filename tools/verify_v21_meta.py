# -*- coding: utf-8 -*-
import json, os, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))
TOKEN = os.environ["GH_TOKEN"]; REPO = "Z1wind/clashlab-overlay"
NAME = "ClashLabAnnotator_Desktop_v2.1.exe"
h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
rels = json.loads(urllib.request.urlopen(urllib.request.Request("https://api.github.com/repos/%s/releases?per_page=20" % REPO, headers=h), timeout=120).read().decode())
rel = next(x for x in rels if x["tag_name"] == "v0.3.7")
a = next(x for x in rel["assets"] if x["name"] == NAME)
print("REMOTE", a["name"], a["size"], a["state"], a["updated_at"], a.get("digest"))
