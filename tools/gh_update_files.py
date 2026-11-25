# -*- coding: utf-8 -*-
"""更新远端 README 两个文件 + 设置 topics（Contents API，单文件提交）。"""
import base64, json, os, urllib.error, urllib.request
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
TOKEN = os.environ["GH_TOKEN"]
REPO = "https://api.github.com/repos/Z1wind/clashlab-overlay"


def call(method, url, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {"Authorization": "token " + TOKEN, "User-Agent": "clashlab", "Accept": "application/vnd.github+json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            body = r.read().decode("utf-8", "ignore")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        return {"_err": e.code, "_body": e.read().decode("utf-8", "ignore")[:300]}


for fn in ("README.md", "README.en.md"):
    with open(os.path.join(BASE, fn), "rb") as f:
        content = base64.b64encode(f.read()).decode()
    cur = call("GET", REPO + "/contents/" + fn)
    sha = cur.get("sha")
    body = {"message": "docs: point to real repository URL and release assets", "content": content, "branch": "main"}
    if sha:
        body["sha"] = sha
    r = call("PUT", REPO + "/contents/" + fn, body)
    print(fn, "->", r.get("commit", {}).get("sha", r.get("_err")), flush=True)

r = call("PATCH", REPO, {"topics": ["clash-of-clans", "overlay", "imgui", "computer-vision", "layout-analysis",
                                    "llm", "research-tool", "python", "mit-license", "game-tools"]})
print("topics:", r.get("topics", r.get("_err")), flush=True)
