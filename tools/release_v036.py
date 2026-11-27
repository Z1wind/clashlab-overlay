# -*- coding: utf-8 -*-
import json, os, sys, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOKEN = os.environ["GH_TOKEN"]; REPO = "Z1wind/clashlab-overlay"
API = "https://api.github.com"; UP = "https://uploads.github.com"
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
TAG, NAME = "v0.3.6", "ClashLab v0.3.6 - one-click battle report + full unit icons + 1080p war capture"
BODY = ("## v0.3.6（2026-11-27）\n\n"
        "- 一键战报：规则评分 + 修复建议 + 穿云箭 + 模拟 + 推荐配比 → HTML（面板「生成战报」按钮）\n"
        "- 兵种/法术真实图标补齐 39/39（含 root-rider、revive）\n"
        "- 1080p 战场侦察抓图流水线（战争地图→敌军→逐基地侦察截图，OCR 状态机+断线重连）\n"
        "- 面板三按钮：打开兵种/法术表、启动标注器、生成战报\n\n"
        "> 启发式分析，非游戏真实引擎；非官方工具，注意 ToS 风险。")
FILES = [("ClashOverlay.exe", os.path.join(BASE, "dist", "ClashOverlay.exe")),
         ("units.html", os.path.join(BASE, "dist", "units.html")),
         ("ClashLabAnnotator.apk", os.path.join(BASE, "dist", "ClashLabAnnotator.apk")),
         ("clashlab_sample_reports_20261127.zip", os.path.join(BASE, "out", "backup", "clashlab_sample_reports_20261127.zip"))]
def req(url, method="GET", data=None, ctype="application/json"):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "clashlab-release", "Accept": "application/vnd.github+json"}
    if data is not None: h["Content-Type"] = ctype
    with urllib.request.urlopen(urllib.request.Request(url, data=data, method=method, headers=h), timeout=900) as r:
        return r.status, json.loads(r.read().decode("utf-8", "ignore"))
rel = None
_, rels = req(API + "/repos/%s/releases?per_page=60" % REPO)
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
