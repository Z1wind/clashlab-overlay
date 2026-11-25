# -*- coding: utf-8 -*-
import json, os, urllib.error, urllib.request
TOKEN = os.environ["GH_TOKEN"]
REPO = "https://api.github.com/repos/Z1wind/clashlab-overlay"

def call(url, accept="application/vnd.github+json"):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": accept}
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=60) as r:
            return json.loads(r.read().decode("utf-8", "ignore"))
    except urllib.error.HTTPError as e:
        return {"_err": e.code}

runs = call(REPO + "/actions/runs?per_page=5")
for w in runs.get("workflow_runs", [])[:4]:
    print("run:", w["name"], w["head_sha"][:8], w["status"], w["conclusion"], flush=True)
top = runs["workflow_runs"][0]
jobs = call(REPO + "/actions/runs/%d/jobs" % top["id"])
for j in jobs.get("jobs", []):
    print("job:", j["name"], j["status"], j["conclusion"], flush=True)
    for s in j.get("steps", []):
        print("   %-32s %s %s" % (s["name"], s["status"], s["conclusion"]), flush=True)
