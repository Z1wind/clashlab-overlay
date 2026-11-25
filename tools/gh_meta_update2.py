# -*- coding: utf-8 -*-
import json, os, urllib.error, urllib.request
TOKEN = os.environ["GH_TOKEN"]; REPO = "https://api.github.com/repos/Z1wind/clashlab-overlay"
def call(m, u, p=None):
    d = json.dumps(p).encode() if p is not None else None
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
    if d: h["Content-Type"] = "application/json"
    try:
        with urllib.request.urlopen(urllib.request.Request(u, data=d, method=m, headers=h), timeout=60) as r:
            b = r.read().decode("utf-8", "ignore"); return json.loads(b) if b else {}
    except urllib.error.HTTPError as e:
        return {"_err": e.code}
desc = ("以 LLM 为辅的部落冲突（Clash of Clans）阵型分析器与基地布局评分工具：侦察截图 → 44×44 标定 → 防守评分 → 弱点 → 战术图 / 2D 俯视图。"
        "进程外 ImGui overlay，零注入只读画面，面向 TH16 阵型；MIT 开源。"
        "An LLM-assisted Clash of Clans base layout analyzer: screenshot -> 44x44 calibration -> scoring -> weak points -> tactical diagram / 2D. Out-of-process overlay, screen-only. MIT.")
print("desc:", bool(call("PATCH", REPO, {"description": desc}).get("description")))
topics = ["clash-of-clans", "base-layout", "layout-analyzer", "th16", "overlay", "imgui", "python",
          "computer-vision", "homography", "opencv", "base-layout-analyzer", "llm", "game-tools",
          "tactical-analysis", "base-design", "windows", "mit-license", "gaming"]
r = call("PUT", REPO + "/topics", {"names": topics})
print("topics:", len(r.get("names", [])), r.get("names", r.get("_err")))
runs = call("GET", REPO + "/actions/runs?per_page=2")
print("runs:", [(x["head_sha"][:8], x["conclusion"]) for x in runs.get("workflow_runs", [])])
