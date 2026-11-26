# -*- coding: utf-8 -*-
import json, os, urllib.request
TOKEN = os.environ["GH_TOKEN"]; REPO = "https://api.github.com/repos/Z1wind/clashlab-overlay"
h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
with urllib.request.urlopen(urllib.request.Request(REPO + "/commits?per_page=2", headers=h), timeout=40) as r:
    for c in json.loads(r.read().decode()):
        print(c["sha"][:8], c["commit"]["message"].splitlines()[0][:90])
