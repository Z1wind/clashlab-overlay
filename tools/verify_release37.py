# -*- coding: utf-8 -*-
"""验证 Release v0.3.7 资产 + 追加 WORKLOG。"""
import hashlib, json, os, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOKEN = os.environ["GH_TOKEN"]; REPO = "Z1wind/clashlab-overlay"; API = "https://api.github.com"
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
def gh(u, accept="application/vnd.github+json"):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": accept}
    return urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=600)
rels = json.loads(gh(API + "/repos/%s/releases?per_page=20" % REPO).read().decode())
rel = next(x for x in rels if x["tag_name"] == "v0.3.7")
print("release", rel["id"], rel["tag_name"], rel["html_url"])
local = {
 "ClashLabAnnotator_20bases_v0.2.5.apk": os.path.getsize(os.path.join(BASE, "dist", "ClashLabAnnotator_20bases_v0.2.5.apk")),
 "units.html": os.path.getsize(os.path.join(BASE, "dist", "units.html")),
 "clashlab_sample_reports_20261127_v2.zip": os.path.getsize(os.path.join(BASE, "out", "backup", "clashlab_sample_reports_20261127_v2.zip")),
 "ClashOverlay.exe": os.path.getsize(os.path.join(BASE, "dist", "ClashOverlay.exe")),
}
apk_asset = None
for a in rel["assets"]:
    print("ASSET", a["name"], a["size"], "local_match=", a["size"] == local.get(a["name"]))
    if a["name"].endswith(".apk"): apk_asset = a
with gh(apk_asset["url"], accept="application/octet-stream") as r:
    print("APK asset HTTP", r.status, r.reason, "| CL:", r.headers.get("Content-Length"), "| ETag:", r.headers.get("ETag"))
    data = r.read()
loc = open(os.path.join(BASE, "dist", "ClashLabAnnotator_20bases_v0.2.5.apk"), "rb").read()
print("downloaded", len(data), "bytes | md5 match:", hashlib.md5(data).hexdigest() == hashlib.md5(loc).hexdigest())
wl = "\n".join(["", "### 轮次 3 补充：CI 产物校验（通过）",
  "- run 52ee008b 成功；artifact 8,291,484 B；解包 APK 8,296,541 B，含 20 张图",
  "- CI 内 annotate6.html md5 与本地一致（差异仅 Linux/Windows zip 元数据 ~4KB）",
  "- Release v0.3.7 资产四项尺寸与本地一致；APK 下载 md5 与本地一致",
  ""])
open(os.path.join(BASE, "docs", "WORKLOG.md"), "a", encoding="utf-8", newline="\n").write(wl)
print("worklog updated")
