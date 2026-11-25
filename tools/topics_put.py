# -*- coding: utf-8 -*-
import json, os, urllib.error, urllib.request
TOKEN = os.environ["GH_TOKEN"]
REPO = "https://api.github.com/repos/Z1wind/clashlab-overlay"

def call(method, url, payload=None, accept="application/vnd.github+json"):
    d = json.dumps(payload).encode() if payload is not None else None
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": accept}
    if d:
        h["Content-Type"] = "application/json"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=d, method=method, headers=h), timeout=60) as r:
            b = r.read().decode("utf-8", "ignore")
            return json.loads(b) if b else {}
    except urllib.error.HTTPError as e:
        return {"_err": e.code, "_body": e.read().decode("utf-8", "ignore")[:200]}

names = ["clash-of-clans", "overlay", "imgui", "computer-vision", "layout-analysis",
         "llm", "research-tool", "python", "mit-license", "game-tools"]
for accept in ("application/vnd.github.mercy-preview+json", "application/vnd.github+json"):
    r = call("PUT", REPO + "/topics", {"names": names}, accept)
    print("PUT /topics ->", r.get("names", r.get("_err")), flush=True)
    if r.get("names"):
        break
repo = call("GET", REPO)
print("repo topics now:", repo.get("topics"), flush=True)
cs = call("GET", REPO + "/commits?per_page=5")
for c in cs[:5]:
    print("commit:", c["sha"][:8], c["commit"]["message"].splitlines()[0][:60], flush=True)
runs = call("GET", REPO + "/actions/runs?per_page=3")
for w in runs.get("workflow_runs", []):
    print("run:", w["head_sha"][:8], w["status"], w["conclusion"], flush=True)
