# -*- coding: utf-8 -*-
import json, os, sys, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOKEN = os.environ["GH_TOKEN"]; REPO = "Z1wind/clashlab-overlay"
API = "https://api.github.com"; UP = "https://uploads.github.com"
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
TAG, NAME = "v0.3.2", "ClashLab v0.3.2 - startup + traditional Chinese fixes"
BODY = ("## v0.3.2（2026-11-27）\n\n"
        "- 修复：双击 exe 看不到窗口 —— 无参数启动现在直接打开 PANEL（主屏可见）\n"
        "- 修复：繁体中文 —— 打包补齐 zhconv 数据；中/繁/EN 切换与 --lang zh-hant 实测正常\n"
        "- 新增 docs/USAGE.md（启动、快捷键、功能前置条件、常见问题）\n"
        "- 交付自测：四页切换、三语、HUD、单实例、draw errors 0\n\n"
        "> 非官方工具；请自行评估 ToS 风险。")
FILES = [("ClashOverlay.exe", os.path.join(BASE, "dist", "ClashOverlay.exe")),
         ("ClashLabAnnotator.apk", os.path.join(BASE, "dist", "ClashLabAnnotator.apk")),
         ("clashlab_sample_reports_20261127.zip", os.path.join(BASE, "out", "backup", "clashlab_sample_reports_20261127.zip"))]
def req(url, method="GET", data=None, ctype="application/json"):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "clashlab-release", "Accept": "application/vnd.github+json"}
    if data is not None: h["Content-Type"] = ctype
    with urllib.request.urlopen(urllib.request.Request(url, data=data, method=method, headers=h), timeout=900) as r:
        return r.status, json.loads(r.read().decode("utf-8", "ignore"))
rel = None
_, rels = req(API + "/repos/%s/releases?per_page=50" % REPO)
for x in rels:
    if x.get("tag_name") == TAG: rel = x; break
if rel is None:
    st, rel = req(API + "/repos/%s/releases" % REPO, "POST",
                  json.dumps({"tag_name": TAG, "name": NAME, "body": BODY, "draft": False, "prerelease": False}).encode())
    print("created", st, rel["id"], flush=True)
rid = rel["id"]; have = {a["name"]: a for a in rel.get("assets") or []}
for name, path in FILES:
    if name in have:
        print("skip", name, have[name]["size"]); continue
    print("upload", name, os.path.getsize(path), flush=True)
    with open(path, "rb") as f: body = f.read()
    st, art = req(UP + "/repos/%s/releases/%d/assets?name=%s" % (REPO, rid, urllib.parse.quote(name)), "POST", body, "application/octet-stream")
    print("  ->", st, art.get("size"), flush=True)
_, rel2 = req(API + "/repos/%s/releases/%d" % (REPO, rid))
for a in rel2.get("assets") or []:
    print("ASSET", a["name"], a["size"], a["state"])
