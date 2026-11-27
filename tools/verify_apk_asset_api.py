# -*- coding: utf-8 -*-
import hashlib, json, os, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOKEN = os.environ["GH_TOKEN"]; REPO = "Z1wind/clashlab-overlay"; API = "https://api.github.com"
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
def gh(u, accept="application/vnd.github+json", raw=False):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": accept}
    with urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=300) as r:
        return r.status, (r.read() if raw else json.loads(r.read().decode("utf-8", "ignore"))), dict(r.headers)
rels = gh(API + "/repos/%s/releases?per_page=10" % REPO)[1]
rel = next(x for x in rels if x["tag_name"] == "v0.3.0")
print("release:", rel["id"], rel["tag_name"], rel["html_url"])
for a in rel["assets"]:
    print("asset", a["name"], a["size"], a["state"])
apk = next(a for a in rel["assets"] if a["name"] == "ClashLabAnnotator.apk")
st, data, hdrs = gh(apk["url"], accept="application/octet-stream", raw=True)
print("API download: HTTP", st, "bytes", len(data), "content-length", hdrs.get("Content-Length"))
local = open(os.path.join(BASE, "dist", "ClashLabAnnotator.apk"), "rb").read()
print("remote md5", hashlib.md5(data).hexdigest())
print("local  md5", hashlib.md5(local).hexdigest(), "match:", hashlib.md5(data).hexdigest() == hashlib.md5(local).hexdigest())
