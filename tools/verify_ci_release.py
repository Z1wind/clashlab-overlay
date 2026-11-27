# -*- coding: utf-8 -*-
"""验证 CI artifact 与 Release v0.3.7 资产。"""
import hashlib, io, json, os, sys, urllib.request, zipfile
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOKEN = os.environ["GH_TOKEN"]; REPO = "Z1wind/clashlab-overlay"; API = "https://api.github.com"
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
def gh(u, accept="application/vnd.github+json"):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": accept}
    return urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=600)
runs = json.loads(gh(API + "/repos/%s/actions/runs?per_page=15" % REPO).read().decode())["workflow_runs"]
run = next(r for r in runs if r["name"] == "build-apk" and r["conclusion"] == "success")
print("CI run:", run["id"], run["head_sha"][:8], run["status"], run["conclusion"], run["created_at"][:19])
arts = json.loads(gh(API + "/repos/%s/actions/runs/%d/artifacts" % (REPO, run["id"])).read().decode())["artifacts"]
for a in arts:
    print("artifact:", a["name"], a["size_in_bytes"], a["expired"])
art = arts[0]
with gh(art["archive_download_url"], accept="application/octet-stream") as r:
    print("artifact HTTP", r.status, r.reason, "| Content-Length:", r.headers.get("Content-Length"))
    zdata = r.read()
print("artifact zip bytes:", len(zdata))
z = zipfile.ZipFile(io.BytesIO(zdata))
print("zip entries:", z.namelist())
apk = z.read([n for n in z.namelist() if n.endswith(".apk")][0])
local = open(os.path.join(BASE, "dist", "ClashLabAnnotator_20bases_v0.2.5.apk"), "rb").read()
print("CI apk bytes:", len(apk), "| md5:", hashlib.md5(apk).hexdigest())
print("local apk bytes:", len(local), "| md5:", hashlib.md5(local).hexdigest(), "| size_equal:", len(apk) == len(local))
# Release 资产
rels = json.loads(gh(API + "/repos/%s/releases?per_page=20" % REPO).read().decode())
rel = next(x for x in rels if x["tag_name"] == "v0.3.7")
print("release:", rel["id"], rel["tag_name"], rel["html_url"])
a2 = next(a for a in rel["assets"] if a["name"] == "ClashLabAnnotator_20bases_v0.2.5.apk")
with gh(a2["url"], accept="application/octet-stream") as r:
    print("asset HTTP", r.status, r.reason, "| Content-Length:", r.headers.get("Content-Length"), "| ETag:", r.headers.get("ETag"))
    data = r.read()
print("downloaded bytes:", len(data), "| md5 match local:", hashlib.md5(data).hexdigest() == hashlib.md5(local).hexdigest())
for a in rel["assets"]:
    print("ASSET", a["name"], a["size"])
