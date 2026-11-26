# -*- coding: utf-8 -*-
import json, os, urllib.request
TOKEN = os.environ["GH_TOKEN"]; REPO = "https://api.github.com/repos/Z1wind/clashlab-overlay"
def get(u):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
    with urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))
runs = get(REPO + "/actions/runs?per_page=2")
for w in runs["workflow_runs"]:
    print("run:", w["head_sha"][:8], w["status"], w["conclusion"])
