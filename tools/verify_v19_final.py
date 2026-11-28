# -*- coding: utf-8 -*-
import hashlib, json, os, subprocess, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOKEN = os.environ["GH_TOKEN"]; REPO = "Z1wind/clashlab-overlay"
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
NAME = "ClashLabAnnotator_Desktop_v1.9.exe"
LOCAL = os.path.join(BASE, "dist", NAME)
loc = open(LOCAL, "rb").read(); loc_md5 = hashlib.md5(loc).hexdigest()
print("LOCAL_FILE", NAME, len(loc), "bytes", "md5", loc_md5, "mtime", os.path.getmtime(LOCAL))
h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
rels = json.loads(urllib.request.urlopen(urllib.request.Request("https://api.github.com/repos/%s/releases?per_page=20" % REPO, headers=h), timeout=60).read().decode())
rel = next(x for x in rels if x["tag_name"] == "v0.3.7")
a = next(x for x in rel["assets"] if x["name"] == NAME)
print("REMOTE_ASSET", a["name"], a["size"], a["state"], a["updated_at"])
h2 = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/octet-stream"}
with urllib.request.urlopen(urllib.request.Request(a["url"], headers=h2), timeout=600) as r:
    print("HTTP", r.status, r.reason, "| CL:", r.headers.get("Content-Length"), "| ETag:", r.headers.get("ETag"), "| Last-Modified:", r.headers.get("Last-Modified"))
    data = r.read()
print("DOWNLOAD", len(data), "bytes | md5", hashlib.md5(data).hexdigest(), "| match_local", hashlib.md5(data).hexdigest() == loc_md5)
# 远端 git HEAD 与本地 HEAD
g = r"E:\Temp\mingit2\cmd\git.exe"
local = subprocess.check_output([g, "-C", BASE, "rev-parse", "HEAD"]).decode().strip()
remote = json.loads(urllib.request.urlopen(urllib.request.Request("https://api.github.com/repos/%s/commits/main" % REPO, headers=h), timeout=60).read().decode())["sha"]
print("GIT local HEAD", local[:12], "| remote main", remote[:12], "| match", local == remote)
