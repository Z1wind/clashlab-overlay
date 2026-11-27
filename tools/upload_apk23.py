# -*- coding: utf-8 -*-
import json, os, sys, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOKEN = os.environ["GH_TOKEN"]; REPO = "Z1wind/clashlab-overlay"
API = "https://api.github.com"; UP = "https://uploads.github.com"
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
NAME = "ClashLabAnnotator_20bases_v0.2.3.apk"; PATH = os.path.join(BASE, "dist", NAME)
def req(url, method="GET", data=None, ctype="application/json"):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "clashlab", "Accept": "application/vnd.github+json"}
    if data is not None: h["Content-Type"] = ctype
    with urllib.request.urlopen(urllib.request.Request(url, data=data, method=method, headers=h), timeout=900) as r:
        return r.status, json.loads(r.read().decode("utf-8", "ignore"))
_, rels = req(API + "/repos/%s/releases?per_page=60" % REPO)
rel = next(x for x in rels if x["tag_name"] == "v0.3.6")
rid = rel["id"]; have = {a["name"]: a for a in rel.get("assets") or []}
if NAME in have:
    print("exists", have[NAME]["size"])
else:
    body = open(PATH, "rb").read()
    st, art = req(UP + "/repos/%s/releases/%d/assets?name=%s" % (REPO, rid, urllib.parse.quote(NAME)),
                  "POST", body, "application/octet-stream")
    print("uploaded", st, art.get("size"))
_, rel2 = req(API + "/repos/%s/releases/%d" % (REPO, rid))
for a in rel2.get("assets") or []:
    print("ASSET", a["name"], a["size"], a["state"])
