# -*- coding: utf-8 -*-
import json, os, time, urllib.request
TOKEN = os.environ["GH_TOKEN"]; REPO = "https://api.github.com/repos/Z1wind/clashlab-overlay"
def req(u, method="GET", payload=None):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
    data = json.dumps(payload).encode() if payload is not None else None
    if data: h["Content-Type"] = "application/json"
    with urllib.request.urlopen(urllib.request.Request(u, data=data, method=method, headers=h), timeout=60) as r:
        b = r.read().decode("utf-8", "ignore")
        return json.loads(b) if b else {}
print("--- remote commits ---")
for c in req(REPO + "/commits?per_page=3"):
    print(c["sha"][:8], c["commit"]["message"].splitlines()[0][:90])
desc = ("An LLM-assisted Clash of Clans base analyzer + wargame + Android annotator: screenshot -> 44x44 "
        "calibration -> scoring -> weak points -> tactical map/2D; synthetic type+level recognition "
        "(type .979 / level MAE 1.14); TH1-TH19 data; wargame + spawn-line optimizer; MIT.")
topics = ["base-design", "base-layout", "clash-of-clans", "computer-vision", "game-tools", "gaming",
          "homography", "imgui", "layout-analyzer", "llm", "mit-license", "opencv", "overlay", "python",
          "tactical-analysis", "th16", "windows", "clashking", "synthetic-data", "level-recognition",
          "android", "battle-simulation", "wargame"]
try:
    m = req(REPO, method="PATCH", payload={"description": desc, "topics": topics})
    print("--- meta updated ---")
    print("desc:", m.get("description")[:120])
    print("topics:", len(m.get("topics") or []))
except Exception as e:
    print("meta update failed:", str(e)[:120])
time.sleep(6)
print("--- runs ---")
for w in req(REPO + "/actions/runs?per_page=3")["workflow_runs"]:
    print(w["created_at"][:16], w["head_sha"][:8], w["status"], w["conclusion"])
