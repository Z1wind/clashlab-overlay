# -*- coding: utf-8 -*-
import base64, json, os, urllib.error, urllib.request
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
TOKEN = os.environ["GH_TOKEN"]
REPO = "https://api.github.com/repos/Z1wind/clashlab-overlay"

# 1) 看 scope
req = urllib.request.Request("https://api.github.com/user", headers={"Authorization": "token " + TOKEN, "User-Agent": "c"})
with urllib.request.urlopen(req, timeout=30) as r:
    print("scopes:", r.headers.get("x-oauth-scopes"), flush=True)

# 2) 推 ci.yml
path = ".github/workflows/ci.yml"
local = open(os.path.join(BASE, ".github", "workflows", "ci.yml"), "rb").read()
payload = {"message": "ci: add GitHub Actions workflow (windows + py3.13 tests)",
           "content": base64.b64encode(local).decode(), "branch": "main"}
cur = None
try:
    with urllib.request.urlopen(urllib.request.Request(REPO + "/contents/" + path,
                                  headers={"Authorization": "token " + TOKEN, "User-Agent": "c"}), timeout=30) as r:
        cur = json.loads(r.read().decode())
except urllib.error.HTTPError as e:
    print("get existing:", e.code, flush=True)
if cur and cur.get("sha"):
    payload["sha"] = cur["sha"]
req = urllib.request.Request(REPO + "/contents/" + path, data=json.dumps(payload).encode(), method="PUT",
                             headers={"Authorization": "token " + TOKEN, "User-Agent": "c",
                                      "Accept": "application/vnd.github+json", "Content-Type": "application/json"})
try:
    with urllib.request.urlopen(req, timeout=60) as r:
        j = json.loads(r.read().decode())
        print("CI PUSH OK commit:", j.get("commit", {}).get("sha"), flush=True)
except urllib.error.HTTPError as e:
    print("CI PUSH FAILED:", e.code, e.read().decode("utf-8", "ignore")[:200], flush=True)
