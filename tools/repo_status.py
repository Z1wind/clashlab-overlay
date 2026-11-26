# -*- coding: utf-8 -*-
import json, os, urllib.request
TOKEN = os.environ["GH_TOKEN"]; REPO = "https://api.github.com/repos/Z1wind/clashlab-overlay"
def req(u, method="GET", payload=None):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
    data = json.dumps(payload).encode() if payload is not None else None
    if data: h["Content-Type"] = "application/json"
    r = urllib.request.Request(u, data=data, method=method, headers=h)
    with urllib.request.urlopen(r, timeout=60) as resp:
        b = resp.read().decode("utf-8", "ignore")
        return json.loads(b) if b else {}
print("--- remote head ---")
for c in req(REPO + "/commits?per_page=3"):
    print(c["sha"][:8], c["commit"]["message"].splitlines()[0][:80])
print("--- runs ---")
for w in req(REPO + "/actions/runs?per_page=3")["workflow_runs"]:
    print(w["created_at"][:16], w["head_sha"][:8], w["status"], w["conclusion"])
print("--- repo meta ---")
m = req(REPO)
print("desc:", m.get("description"))
print("topics:", m.get("topics"))
print("homepage:", m.get("homepage"))
