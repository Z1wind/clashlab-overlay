# -*- coding: utf-8 -*-
"""下载 CI job 日志（手动跟随 302）。"""
import io, json, os, sys, urllib.request, zipfile
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOKEN = os.environ["GH_TOKEN"]; REPO = "Z1wind/clashlab-overlay"; API = "https://api.github.com"
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
def gh_json(u):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
    return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60).read().decode())
runs = gh_json(API + "/repos/%s/actions/runs?per_page=10" % REPO)["workflow_runs"]
run = next(r for r in runs if r["name"] == "build-apk")
jobs = gh_json(API + "/repos/%s/actions/runs/%d/jobs" % (REPO, run["id"]))["jobs"]
for j in jobs:
    print("job", j["id"], j["name"], j["conclusion"])
    for s in j["steps"]:
        print("  step:", s["name"], s["conclusion"])
job = jobs[0]
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k): return None
op = urllib.request.build_opener(NoRedirect)
req = urllib.request.Request(API + "/repos/%s/actions/jobs/%d/logs" % (REPO, job["id"]),
                             headers={"Authorization": "token " + TOKEN, "Accept": "application/vnd.github+json"})
try:
    op.open(req, timeout=60)
except urllib.error.HTTPError as e:
    loc = e.headers.get("Location")
    print("redirect:", e.code, "loc?", bool(loc))
    if loc:
        with urllib.request.urlopen(urllib.request.Request(loc, headers={"User-Agent": "c"}), timeout=120) as r:
            data = r.read()
        print("log zip bytes:", len(data))
        z = zipfile.ZipFile(io.BytesIO(data))
        text = "\n".join(z.read(n).decode("utf-8", "replace") for n in z.namelist())
        for line in text.splitlines():
            if any(k in line for k in ("sha256", "ClashLabAnnotator.apk", "BUILD_OK", "error", "Error", "assets")):
                print("LOG:", line[:200])
