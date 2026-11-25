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
        return {"_err": e.code, "_body": e.read().decode("utf-8", "ignore")[:200]}

runs = call(REPO + "/actions/runs?per_page=1")
run = runs["workflow_runs"][0]
print("run:", run["id"], run["name"], run["status"], run["conclusion"], flush=True)
jobs = call(REPO + "/actions/runs/%d/jobs" % run["id"])
for j in jobs.get("jobs", []):
    print("job:", j["name"], j["status"], j["conclusion"], flush=True)
    for s in j.get("steps", []):
        print("   step: %-40s %s %s" % (s["name"], s["status"], s["conclusion"]), flush=True)
