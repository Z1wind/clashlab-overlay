# -*- coding: utf-8 -*-
import json, os, urllib.request, time
TOKEN = os.environ["GH_TOKEN"]; REPO = "https://api.github.com/repos/Z1wind/clashlab-overlay"
def get(u):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
    with urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))
runs = get(REPO + "/actions/runs?per_page=12")["workflow_runs"]
for w in runs:
    print("%s %-8s %-10s %s" % (w["created_at"][:16], w["head_sha"][:8], str(w["conclusion"]), (w["display_title"] or "")[:60]))
print("---- 最新一次失败详情 ----")
failed = [w for w in runs if w["conclusion"] == "failure"]
if failed:
    w = failed[0]
    print("run:", w["id"], w["head_sha"][:8], w["created_at"])
    jobs = get(REPO + "/actions/runs/%d/jobs" % w["id"])["jobs"]
    for j in jobs:
        print("job:", j["name"], j["conclusion"])
        for s in j.get("steps", []):
            if s.get("conclusion") not in ("success", "skipped", None):
                print("   step:", s["name"], s["conclusion"])
