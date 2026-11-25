# -*- coding: utf-8 -*-
import json, os, time, urllib.error, urllib.request
TOKEN = os.environ["GH_TOKEN"]
REPO = "https://api.github.com/repos/Z1wind/clashlab-overlay"

def call(method, url, payload=None, accept="application/vnd.github+json"):
    data = json.dumps(payload).encode() if payload is not None else None
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": accept}
    if data is not None:
        h["Content-Type"] = "application/json"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data, method=method, headers=h), timeout=60) as r:
            b = r.read().decode("utf-8", "ignore")
            return json.loads(b) if b else {}
    except urllib.error.HTTPError as e:
        return {"_err": e.code, "_body": e.read().decode("utf-8", "ignore")[:200]}

topics = ["clash-of-clans", "overlay", "imgui", "computer-vision", "layout-analysis",
          "llm", "research-tool", "python", "mit-license"]
for accept in ("application/vnd.github.mercy-preview+json", "application/vnd.github+json"):
    r = call("PATCH", REPO, {"topics": topics}, accept=accept)
    print("PATCH topics with", accept, "->", r.get("topics", r.get("_err")), flush=True)
    if r.get("topics"):
        break
runs = call("GET", REPO + "/actions/runs?per_page=3")
if isinstance(runs, dict) and runs.get("workflow_runs") is not None:
    for w in runs["workflow_runs"][:3]:
        print("run:", w["name"], w.get("status"), w.get("conclusion"), w["head_sha"][:8], flush=True)
else:
    print("runs:", runs, flush=True)
