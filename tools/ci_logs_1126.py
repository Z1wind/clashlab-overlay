# -*- coding: utf-8 -*-
import io, json, os, urllib.request, zipfile
TOKEN = os.environ["GH_TOKEN"]; REPO = "https://api.github.com/repos/Z1wind/clashlab-overlay"
def get(url, raw=False):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=120) as r:
        return r.read() if raw else json.loads(r.read().decode())
runs = get(REPO + "/actions/runs?per_page=1")
run = runs["workflow_runs"][0]
print("run:", run["id"], run["head_sha"][:8], run["conclusion"])
jobs = get(REPO + "/actions/runs/%d/jobs" % run["id"])["jobs"]
for j in jobs:
    print("job:", j["name"], j["conclusion"])
    for s in j.get("steps", []):
        print("   ", s["name"], s["conclusion"])
logs = get(REPO + "/actions/runs/%d/logs" % run["id"], raw=True)
z = zipfile.ZipFile(io.BytesIO(logs))
for name in z.namelist():
    if name.endswith("test.txt") or "test" in name:
        txt = z.read(name).decode("utf-8", "replace")
        print("=" * 20, name)
        for line in txt.splitlines():
            if any(k in line for k in ("ERROR", "FAIL", "Ran ", "Error", "Traceback", "assert", "ModuleNotFound")):
                print(line.encode("ascii", "replace").decode()[:200])
        break
