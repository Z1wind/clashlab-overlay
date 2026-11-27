# -*- coding: utf-8 -*-
import hashlib, json, os, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOKEN = os.environ["GH_TOKEN"]; REPO = "Z1wind/clashlab-overlay"; API = "https://api.github.com"
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
def gh(u, accept="application/vnd.github+json"):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "clashlab", "Accept": accept}
    return urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=600)
with gh(API + "/repos/%s/releases?per_page=50" % REPO) as r:
    rels = json.loads(r.read().decode())
rel = next(x for x in rels if x["tag_name"] == "v0.3.2")
apk = next(a for a in rel["assets"] if a["name"] == "ClashLabAnnotator.apk")
zipa = next(a for a in rel["assets"] if a["name"].endswith(".zip"))
print("release", rel["id"], rel["tag_name"], rel["html_url"])
for a in rel["assets"]:
    print("ASSET", a["name"], a["size"], a["state"])
with gh(zipa["url"], accept="application/octet-stream") as r:
    print("HTTP", r.status, r.reason)
    for k in ("Content-Type", "Content-Length", "Date", "ETag", "Last-Modified"):
        v = r.headers.get(k)
        if v: print(k + ":", v)
    data = r.read()
print("actual bytes:", len(data))
localz = open(os.path.join(BASE, "out", "backup", "clashlab_sample_reports_20261127.zip"), "rb").read()
print("remote md5:", hashlib.md5(data).hexdigest())
print("local  md5:", hashlib.md5(localz).hexdigest(), "match:", hashlib.md5(data).hexdigest() == hashlib.md5(localz).hexdigest())
localexe = os.path.join(BASE, "dist", "ClashOverlay.exe")
print("local exe:", os.path.getsize(localexe), hashlib.md5(open(localexe, "rb").read()).hexdigest())
exeasset = next(a for a in rel["assets"] if a["name"] == "ClashOverlay.exe")
print("remote exe size:", exeasset["size"], "local_equal:", exeasset["size"] == os.path.getsize(localexe))
