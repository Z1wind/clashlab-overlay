# -*- coding: utf-8 -*-
import json, os, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOKEN = os.environ["GH_TOKEN"]; REPO = "Z1wind/clashlab-overlay"; API = "https://api.github.com"
def gh(u):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
    return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60).read().decode())
runs = gh(API + "/repos/%s/actions/runs?per_page=8" % REPO)["workflow_runs"]
for r in runs[:6]:
    print(r["name"], r["head_sha"][:8], r["status"], r["conclusion"], r["created_at"][:19])
for r in runs:
    if r["name"] == "build-apk":
        arts = gh(API + "/repos/%s/actions/runs/%d/artifacts" % (REPO, r["id"]))["artifacts"]
        print("run", r["id"], r["head_sha"][:8], r["status"], r["conclusion"],
              "| artifact:", [(a["name"], a["size_in_bytes"]) for a in arts])
        break
