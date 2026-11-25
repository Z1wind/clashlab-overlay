# -*- coding: utf-8 -*-
import base64, difflib, json, os, urllib.request
TOKEN = os.environ["GH_TOKEN"]
REPO = "https://api.github.com/repos/Z1wind/clashlab-overlay"

def get(url):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))

remote = get(REPO + "/contents/README.md")
rb = base64.b64decode(remote["content"].replace("\n", "")).decode("utf-8", "replace")
local = open(r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\README.md", encoding="utf-8").read()
print("remote README bytes:", len(rb.encode()), "| local:", len(local.encode()))
diff = list(difflib.unified_diff(local.splitlines(), rb.splitlines(), "local", "remote", lineterm="", n=1))
print("diff lines:", len(diff))
for l in diff[:60]:
    print(l.encode("ascii", "replace").decode()[:160])
