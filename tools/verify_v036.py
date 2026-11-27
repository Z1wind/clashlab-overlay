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
print("release", rel["id"], rel["tag_name"], rel["html_url"])
local = {"ClashOverlay.exe": os.path.getsize(os.path.join(BASE, "dist", "ClashOverlay.exe")),
         "units.html": os.path.getsize(os.path.join(BASE, "dist", "units.html")),
         "ClashLabAnnotator.apk": os.path.getsize(os.path.join(BASE, "dist", "ClashLabAnnotator.apk")),
         "clashlab_sample_reports_20261127.zip": os.path.getsize(os.path.join(BASE, "out", "backup", "clashlab_sample_reports_20261127.zip"))}
uni = None
for a in rel["assets"]:
    print("ASSET", a["name"], a["size"], a["state"], "local_match=", a["size"] == local.get(a["name"]))
    if a["name"] == "units.html": uni = a
with gh(uni["url"], accept="application/octet-stream") as r:
    print("HTTP", r.status, r.reason, "| Content-Length:", r.headers.get("Content-Length"))
    data = r.read()
localu = open(os.path.join(BASE, "dist", "units.html"), "rb").read()
print("actual bytes:", len(data), "| units md5 match:", hashlib.md5(data).hexdigest() == hashlib.md5(localu).hexdigest())
for c in json.loads(gh(API + "/repos/%s/commits?per_page=1" % REPO).read().decode()):
    print("remote:", c["sha"][:8], c["commit"]["message"].splitlines()[0][:60])
for w in json.loads(gh(API + "/repos/%s/actions/runs?per_page=2" % REPO).read().decode())["workflow_runs"]:
    print("CI:", w["created_at"][:16], w["head_sha"][:8], w["status"], w["conclusion"])
