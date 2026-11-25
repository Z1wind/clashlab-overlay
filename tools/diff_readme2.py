# -*- coding: utf-8 -*-
import base64, difflib, json, os, urllib.request
TOKEN = os.environ["GH_TOKEN"]
REPO = "https://api.github.com/repos/Z1wind/clashlab-overlay"

def get(url):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))

rb = base64.b64decode(get(REPO + "/contents/README.md")["content"].replace("\n", "")).decode("utf-8", "replace")
local = open(r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\README.md", encoding="utf-8").read()
diff = "\n".join(difflib.unified_diff(local.splitlines(), rb.splitlines(), "local", "remote", lineterm="", n=2))
open(r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\release\readme_diff.txt", "w", encoding="utf-8").write(diff)
print("written", len(diff))
