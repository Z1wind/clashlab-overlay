# -*- coding: utf-8 -*-
import base64, json, os, time, urllib.error, urllib.request
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
TOKEN = os.environ["GH_TOKEN"]
REPO = "https://api.github.com/repos/Z1wind/clashlab-overlay"

def call(method, url, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
    if data is not None:
        h["Content-Type"] = "application/json"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data, method=method, headers=h), timeout=60) as r:
            b = r.read().decode("utf-8", "ignore")
            return json.loads(b) if b else {}
    except urllib.error.HTTPError as e:
        return {"_err": e.code, "_body": e.read().decode("utf-8", "ignore")[:200]}

path = ".github/workflows/ci.yml"
local = open(os.path.join(BASE, ".github", "workflows", "ci.yml"), "rb").read()
cur = call("GET", REPO + "/contents/" + path)
payload = {"message": "ci: force UTF-8 output (fix cp1252 UnicodeEncodeError for Chinese prints)",
           "content": base64.b64encode(local).decode(), "branch": "main"}
if cur.get("sha"):
    payload["sha"] = cur["sha"]
r = call("PUT", REPO + "/contents/" + path, payload)
print("push:", r.get("commit", {}).get("sha", r), flush=True)
