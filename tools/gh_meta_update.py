# -*- coding: utf-8 -*-
"""更新 GitHub 仓库 description / topics（关键词推流）。"""
import json, os, urllib.error, urllib.request
TOKEN = os.environ["GH_TOKEN"]
REPO = "https://api.github.com/repos/Z1wind/clashlab-overlay"

def call(method, url, payload=None):
    d = json.dumps(payload).encode() if payload is not None else None
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
    if d: h["Content-Type"] = "application/json"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=d, method=method, headers=h), timeout=60) as r:
            b = r.read().decode("utf-8", "ignore")
            return json.loads(b) if b else {}
    except urllib.error.HTTPError as e:
        return {"_err": e.code, "_body": e.read().decode("utf-8", "ignore")[:300]}

desc = ("开源部落冲突阵型研究工具：侦察截图 → 44×44 标定 → 防守评分与弱点 → 战术图 / 2D 阵型。"
        "Clash of Clans base layout analyzer & defense scorer (open source, no game injection).")
r = call("PATCH", REPO, {"description": desc,
                          "homepage": "https://github.com/Z1wind/clashlab-overlay"})
print("desc:", r.get("description", r.get("_err")), flush=True)
topics = ["clash-of-clans", "clash-of-clans-layout", "base-layout", "layout-analyzer", "base-analysis",
          "th16", "town-hall-16", "defense-score", "game-analysis", "computer-vision",
          "overlay", "imgui", "python", "open-source", "research-tool", "gaming-tools",
          "mit-license", "strategy", "game-ai", "clash"]
r = call("PUT", REPO + "/topics", {"names": topics})
print("topics:", r.get("names", r.get("_err")), flush=True)
