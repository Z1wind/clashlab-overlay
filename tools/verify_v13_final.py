# -*- coding: utf-8 -*-
import hashlib, json, os, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOKEN = os.environ["GH_TOKEN"]; REPO = "Z1wind/clashlab-overlay"
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
NAME = "ClashLabAnnotator_Desktop_v1.3.exe"
LOCAL = os.path.join(BASE, "dist", NAME)
loc = open(LOCAL, "rb").read()
loc_md5 = hashlib.md5(loc).hexdigest()
print("LOCAL bytes", len(loc), "md5", loc_md5, "mtime", os.path.getmtime(LOCAL))
h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
rels = json.loads(urllib.request.urlopen(urllib.request.Request("https://api.github.com/repos/%s/releases?per_page=20" % REPO, headers=h), timeout=60).read().decode())
rel = next(x for x in rels if x["tag_name"] == "v0.3.7")
a = next(x for x in rel["assets"] if x["name"] == NAME)
print("ASSET", a["name"], "size", a["size"], "state", a["state"], "updated_at", a["updated_at"])
h2 = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/octet-stream"}
with urllib.request.urlopen(urllib.request.Request(a["url"], headers=h2), timeout=600) as r:
    print("HTTP", r.status, r.reason, "| Content-Length:", r.headers.get("Content-Length"), "| ETag:", r.headers.get("ETag"), "| Last-Modified:", r.headers.get("Last-Modified"), "| Content-Type:", r.headers.get("Content-Type"))
    data = r.read()
print("DOWNLOADED", len(data), "bytes | remote md5", hashlib.md5(data).hexdigest(), "| match_local", hashlib.md5(data).hexdigest() == loc_md5)
# smoke artifacts
sr = os.path.join(BASE, "dist_exe", "smoke2_result.json")
if os.path.exists(sr):
    print("SMOKE2", open(sr, encoding="utf-8").read().strip())
s1 = os.path.join(BASE, "dist_exe", "smoke_result.json")
if os.path.exists(s1):
    print("SMOKE1", open(s1, encoding="utf-8").read().strip())
