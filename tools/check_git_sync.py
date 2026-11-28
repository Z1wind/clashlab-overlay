# -*- coding: utf-8 -*-
import json, os, subprocess, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOKEN = os.environ["GH_TOKEN"]; REPO = "Z1wind/clashlab-overlay"
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
g = r"E:\Temp\mingit2\cmd\git.exe"
local = subprocess.check_output([g, "-C", BASE, "rev-parse", "HEAD"]).decode().strip()
url = "https://api.github.com/repos/%s/commits/main" % REPO
h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
remote = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=60).read().decode())["sha"]
print("GIT local HEAD", local, "| remote main", remote, "| match", local == remote)
st = subprocess.check_output([g, "-C", BASE, "status", "--short"]).decode().strip()
print("GIT status:", "(clean)" if not st else st[:300])
