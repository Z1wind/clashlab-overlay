# -*- coding: utf-8 -*-
"""上传 GitHub Release 备份：exe + 标注/战图 zip。幂等：已存在同名 release 则复用。"""
import json, os, sys, urllib.request, urllib.error
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOKEN = os.environ["GH_TOKEN"]
REPO = "Z1wind/clashlab-overlay"
API = "https://api.github.com"
UP = "https://uploads.github.com"
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
TAG = "backup-2026-11-26"
NAME = "ClashLab WIP backup 2026-11-26"
BODY = ("Daily backup (source lives on main). Assets: "
        "ClashOverlay.exe (Windows overlay, bundled OCR) and annotated/real-war data zip.\n\n"
        "Source: https://github.com/Z1wind/clashlab-overlay/tree/main\n"
        "Status/TODO: docs/STATUS.md")
FILES = [("ClashOverlay.exe", os.path.join(BASE, "dist", "ClashOverlay.exe")),
         ("clashlab_annotated_20261126.zip", os.path.join(BASE, "out", "backup", "clashlab_annotated_20261126.zip"))]

def req(url, method="GET", data=None, ctype="application/json", headers=None):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "clashlab-backup", "Accept": "application/vnd.github+json"}
    if headers:
        h.update(headers)
    if data is not None:
        h["Content-Type"] = ctype
    r = urllib.request.Request(url, data=data, method=method, headers=h)
    with urllib.request.urlopen(r, timeout=600) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8", "ignore"))

# 1) 找已有 release
rel = None
try:
    _, rels = req(API + "/repos/%s/releases?per_page=20" % REPO)
    for x in rels:
        if x.get("tag_name") == TAG:
            rel = x
            break
except Exception as e:
    print("list release err:", str(e)[:100])

if rel is None:
    st, rel = req(API + "/repos/%s/releases" % REPO, "POST",
                  json.dumps({"tag_name": TAG, "name": NAME, "body": BODY,
                              "draft": False, "prerelease": True}).encode())
    print("created release", st, rel.get("id"))
else:
    print("release exists", rel.get("id"))

rid = rel["id"]
have = {a["name"]: a for a in rel.get("assets") or []}
for name, path in FILES:
    if name in have:
        print("asset exists:", name, have[name]["size"])
        continue
    size = os.path.getsize(path)
    print("uploading", name, size, "bytes ...", flush=True)
    with open(path, "rb") as f:
        body = f.read()
    st, art = req(UP + "/repos/%s/releases/%d/assets?name=%s" % (REPO, rid, urllib.parse.quote(name)),
                  "POST", body, "application/octet-stream")
    print("uploaded", name, "->", st, "id", art.get("id"), "size", art.get("size"), flush=True)

# 2) 复核
st, rel2 = req(API + "/repos/%s/releases/%d" % (REPO, rid))
print("RELEASE", rel2.get("tag_name"), "assets:")
for a in rel2.get("assets") or []:
    print("  ", a["name"], a["size"], a["state"], a["browser_download_url"])
