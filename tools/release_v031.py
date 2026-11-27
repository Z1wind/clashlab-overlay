# -*- coding: utf-8 -*-
"""v0.3.1 Release：exe + APK + 样例报告 zip。"""
import json, os, sys, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOKEN = os.environ["GH_TOKEN"]; REPO = "Z1wind/clashlab-overlay"
API = "https://api.github.com"; UP = "https://uploads.github.com"
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
TAG, NAME = "v0.3.1", "ClashLab v0.3.1 - sample reports + one-command pipeline"
BODY = ("## v0.3.1（2026-11-27）\n\n"
        "- 新增 tools/report_one.py：一条命令出评分报告 + 俯视箭线图 + Markdown 摘要\n"
        "- 新增 docs/SAMPLE_REPORT.md：6 套 TH16 阵样例（评分 52.4–63.7，每阵 3 条箭线候选）\n"
        "- 修复：PANEL 点击不切换、设置/研究页重叠、单实例互斥；手机标注 APK v2\n"
        "- 训练数据排除 firespitter；检测器/自动标注按预注册判据失败并归档\n\n"
        "> 非官方工具，请自行评估 ToS 风险。")
FILES = [("ClashOverlay.exe", os.path.join(BASE, "dist", "ClashOverlay.exe")),
         ("ClashLabAnnotator.apk", os.path.join(BASE, "dist", "ClashLabAnnotator.apk")),
         ("clashlab_sample_reports_20261127.zip", os.path.join(BASE, "out", "backup", "clashlab_sample_reports_20261127.zip"))]
def req(url, method="GET", data=None, ctype="application/json"):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "clashlab-release", "Accept": "application/vnd.github+json"}
    if data is not None: h["Content-Type"] = ctype
    with urllib.request.urlopen(urllib.request.Request(url, data=data, method=method, headers=h), timeout=900) as r:
        return r.status, json.loads(r.read().decode("utf-8", "ignore"))
rel = None
_, rels = req(API + "/repos/%s/releases?per_page=40" % REPO)
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
