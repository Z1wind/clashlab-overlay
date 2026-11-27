# -*- coding: utf-8 -*-
import hashlib, json, os, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOKEN = os.environ["GH_TOKEN"]; REPO = "Z1wind/clashlab-overlay"; API = "https://api.github.com"
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
def gh(u, accept="application/vnd.github+json"):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "clashlab", "Accept": accept}
    req = urllib.request.Request(u, headers=h)
    return urllib.request.urlopen(req, timeout=300)
with gh(API + "/repos/%s/releases?per_page=10" % REPO) as r:
    rels = json.loads(r.read().decode())
rel = next(x for x in rels if x["tag_name"] == "v0.3.0")
apk = next(a for a in rel["assets"] if a["name"] == "ClashLabAnnotator.apk")
print("RELEASE", rel["tag_name"], rel["html_url"])
print("ASSET", apk["name"], apk["size"], apk["state"])
with gh(apk["url"], accept="application/octet-stream") as r:
    print("HTTP", r.status, r.reason)
    for k in ("Content-Type", "Content-Length", "Date", "ETag", "Last-Modified"):
        v = r.headers.get(k)
        if v: print(k + ":", v)
    data = r.read()
    print("actual bytes:", len(data))
local = open(os.path.join(BASE, "dist", "ClashLabAnnotator.apk"), "rb").read()
print("remote md5:", hashlib.md5(data).hexdigest())
print("local  md5:", hashlib.md5(local).hexdigest(), "match:", hashlib.md5(data).hexdigest() == hashlib.md5(local).hexdigest())
