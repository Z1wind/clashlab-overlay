# -*- coding: utf-8 -*-
import json, os, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOKEN = os.environ["GH_TOKEN"]
def gh(u):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
    return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60).read().decode())
runs = gh("https://api.github.com/repos/Z1wind/clashlab-overlay/actions/runs?per_page=6")
for r in runs.get("workflow_runs", []):
    print(r["name"], r["head_sha"][:8], r["status"], r["conclusion"], r["created_at"][:19])
