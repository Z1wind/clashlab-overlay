# -*- coding: utf-8 -*-
import io, json, os, sys, urllib.request, zipfile
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOKEN = os.environ["GH_TOKEN"]; REPO = "Z1wind/clashlab-overlay"; API = "https://api.github.com"
def req(url, headers, follow=False):
    try:
        return urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=120)
    except urllib.error.HTTPError as e:
        return e
h = {"Authorization": "token " + TOKEN, "Accept": "application/vnd.github+json", "User-Agent": "c"}
runs = json.loads(req(API + "/repos/%s/actions/runs?per_page=10" % REPO, h).read().decode())["workflow_runs"]
run = next(r for r in runs if r["name"] == "build-apk")
jobs = json.loads(req(API + "/repos/%s/actions/runs/%d/jobs" % (REPO, run["id"]), h).read().decode())["jobs"]
for j in jobs:
    print("JOB", j["name"], j["conclusion"], "steps:", [(s["name"], s["conclusion"]) for s in j["steps"]])
job = jobs[0]
r = req(API + "/repos/%s/actions/jobs/%d/logs" % (REPO, job["id"]), {**h, "Accept": "application/json"})
print("logs resp:", getattr(r, "status", None) or r.code)
if isinstance(r, urllib.error.HTTPError) and r.code in (301, 302, 303, 307, 308):
    loc = r.headers.get("Location")
    print("redirect to:", (loc or "")[:80])
    for hh in ({**h}, {"User-Agent": "c"}):
        r2 = req(loc, hh)
        if hasattr(r2, "status") and r2.status == 200:
            data = r2.read()
            print("downloaded bytes:", len(data))
            try:
                z = zipfile.ZipFile(io.BytesIO(data))
                text = "\n".join(z.read(n).decode("utf-8", "replace") for n in z.namelist())
                for line in text.splitlines():
                    if any(k in line for k in ("sha256", "ClashLabAnnotator.apk", "BUILD_OK", "rror", "assets", "ls -l")):
                        print("LOG:", line[:220])
                break
            except Exception as e:
                print("not zip:", str(e)[:80], data[:80])
