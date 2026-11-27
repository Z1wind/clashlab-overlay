# -*- coding: utf-8 -*-
import hashlib, json, os, urllib.request, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOKEN = os.environ["GH_TOKEN"]; REPO = "Z1wind/clashlab-overlay"; API = "https://api.github.com"
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
def gh(u, accept="application/vnd.github+json"):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": accept}
    return urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=600)
with gh(API + "/repos/%s/releases?per_page=60" % REPO) as r:
    rels = json.loads(r.read().decode())
rel = next(x for x in rels if x["tag_name"] == "v0.3.6")
a2 = next(a for a in rel["assets"] if a["name"].endswith("_v2.zip"))
with gh(a2["url"], accept="application/octet-stream") as r:
    print("HTTP", r.status, r.reason, "| Content-Length:", r.headers.get("Content-Length"))
    data = r.read()
local = open(os.path.join(BASE, "out", "backup", "clashlab_sample_reports_20261127_v2.zip"), "rb").read()
print("actual bytes:", len(data), "| md5 match:", hashlib.md5(data).hexdigest() == hashlib.md5(local).hexdigest())
import zipfile
z = zipfile.ZipFile(os.path.join(BASE, "out", "backup", "clashlab_sample_reports_20261127_v2.zip"))
print("entries:", len(z.infolist()), "| battle htmls:", len([n for n in z.namelist() if n.startswith("reports/")]))
