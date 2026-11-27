# -*- coding: utf-8 -*-
import json, os, sys, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOKEN = os.environ["GH_TOKEN"]; REPO = "Z1wind/clashlab-overlay"
API = "https://api.github.com"; UP = "https://uploads.github.com"
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
TAG, NAME = "v0.3.3", "ClashLab v0.3.3 - heuristic battle sim + rule scoring + annotator v3"
BODY = ("## v0.3.3（2026-11-27）\n\n"
        "- 新增 clashlab/battle_sim.py + tools/sim_attack.py：启发式战斗模拟（Dijkstra 寻路/防御 DPS 暴露/生存率/拆本时间/星级估算）\n"
        "- 新增 layout_grid/layout_rules：44×44 布局层 + 8 条可解释规则评分\n"
        "- 新增 auto_report/self_check：一条命令出报告、防守自检+推荐打法+模拟\n"
        "- 标注器 v3：四角吸附、箭线预览（A）、保存并出报告（R）\n"
        "- ClashKing 免费端点集成：成员 TH（cached）、战争筛选、静态数据 max-level；面板显示部落 TH 分布\n\n"
        "> 战斗模拟为启发式估算，非游戏真实引擎；非官方工具，请自行评估 ToS 风险。")
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
