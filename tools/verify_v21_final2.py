# -*- coding: utf-8 -*-
import hashlib, json, os, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))
TOKEN = os.environ["GH_TOKEN"]; REPO = "Z1wind/clashlab-overlay"
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
NAME = "ClashLabAnnotator_Desktop_v2.1.exe"
LOCAL = os.path.join(BASE, "dist", NAME)
data = open(LOCAL, "rb").read()
print("LOCAL_FILE", len(data), "bytes md5", hashlib.md5(data).hexdigest().upper(), "sha256", hashlib.sha256(data).hexdigest(), "mtime", os.path.getmtime(LOCAL))
h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
rels = json.loads(urllib.request.urlopen(urllib.request.Request("https://api.github.com/repos/%s/releases?per_page=20" % REPO, headers=h), timeout=120).read().decode())
rel = next(x for x in rels if x["tag_name"] == "v0.3.7")
a = next(x for x in rel["assets"] if x["name"] == NAME)
print("REMOTE_ASSET size", a["size"], "state", a["state"], "updated_at", a["updated_at"], "digest", a.get("digest"))
h2 = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/octet-stream", "Range": "bytes=0-1048575"}
with urllib.request.urlopen(urllib.request.Request(a["url"], headers=h2), timeout=300) as r:
    print("HTTP", r.status, r.reason, "| CL:", r.headers.get("Content-Length"), "| Content-Range:", r.headers.get("Content-Range"), "| ETag:", r.headers.get("ETag"), "| Last-Modified:", r.headers.get("Last-Modified"))
    chunk = r.read()
print("FIRST_MB_MATCH", hashlib.md5(chunk).hexdigest() == hashlib.md5(data[:len(chunk)]).hexdigest(), hashlib.md5(chunk).hexdigest())
