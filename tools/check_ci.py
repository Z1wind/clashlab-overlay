# -*- coding: utf-8 -*-
import json, os, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOKEN = os.environ["GH_TOKEN"]
def gh(u):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
    return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60).read().decode())
print("head:", gh("https://api.github.com/repos/Z1wind/clashlab-overlay/commits?per_page=1")[0]["sha"][:8])
try:
    wf = gh("https://api.github.com/repos/Z1wind/clashlab-overlay/actions/workflows")
    for w in wf.get("workflows", []):
        print("workflow:", w["name"], w["path"], w["state"])
except Exception as e:
    print("workflows err", str(e)[:150])
try:
    runs = gh("https://api.github.com/repos/Z1wind/clashlab-overlay/actions/runs?per_page=5")
    print("runs:", runs.get("total_count"))
    for r in runs.get("workflow_runs", [])[:5]:
        print(" ", r["name"], r["head_sha"][:8], r["status"], r["conclusion"], r["created_at"][:19])
except Exception as e:
    print("runs err", str(e)[:150])
