# -*- coding: utf-8 -*-
import hashlib, json, os, sys, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOKEN = os.environ["GH_TOKEN"]; REPO = "Z1wind/clashlab-overlay"
API = "https://api.github.com"; UP = "https://uploads.github.com"
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
NAME = "ClashLabAnnotator_Desktop_v1.4.exe"; PATH = os.path.join(BASE, "dist", NAME)
def req(url, method="GET", data=None, ctype="application/json"):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "clashlab", "Accept": "application/vnd.github+json"}
    if data is not None: h["Content-Type"] = ctype
    with urllib.request.urlopen(urllib.request.Request(url, data=data, method=method, headers=h), timeout=900) as r:
        body = r.read().decode("utf-8", "ignore")
        return r.status, (json.loads(body) if body else {})
_, rels = req(API + "/repos/%s/releases?per_page=20" % REPO)
rel = next(x for x in rels if x["tag_name"] == "v0.3.7"); rid = rel["id"]
have = {a["name"]: a for a in rel.get("assets") or []}
if NAME in have: req(have[NAME]["url"], "DELETE"); print("deleted old")
body = open(PATH, "rb").read()
st, art = req(UP + "/repos/%s/releases/%d/assets?name=%s" % (REPO, rid, urllib.parse.quote(NAME)), "POST", body, "application/octet-stream")
print("uploaded", st, art.get("size"))
_, rel2 = req(API + "/repos/%s/releases/%d" % (REPO, rid))
a = next(x for x in rel2["assets"] if x["name"] == NAME)
h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/octet-stream"}
with urllib.request.urlopen(urllib.request.Request(a["url"], headers=h), timeout=900) as r:
    print("download HTTP", r.status, r.reason, "| CL:", r.headers.get("Content-Length"))
    data = r.read()
loc = open(PATH, "rb").read()
print("downloaded", len(data), "| md5 match:", hashlib.md5(data).hexdigest() == hashlib.md5(loc).hexdigest(), "| md5", hashlib.md5(data).hexdigest())



