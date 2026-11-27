# -*- coding: utf-8 -*-
"""v0.3.0 Release：exe + 手机标注 APK + 标注数据 zip。"""
import json, os, sys, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOKEN = os.environ["GH_TOKEN"]
REPO = "Z1wind/clashlab-overlay"
API = "https://api.github.com"; UP = "https://uploads.github.com"
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
TAG = "v0.3.0"; NAME = "ClashLab v0.3.0 - 手机标注器 + 纯本地分析"
BODY = ("## v0.3.0（2026-11-27）\n\n"
        "- 新增：手机标注 APK（内置 3 张真实战图，4 角标定 + 建筑点选 + JSON 导出）\n"
        "- 修复：PANEL 点击不切换（去双鼠标通道）、研究/设置页重叠、调试锚点默认隐藏\n"
        "- 单实例互斥；HUD 穿云箭绘制已实机验证\n"
        "- 方向调整：ClashKing/CoC API 通道关闭（对方明确拒绝），主线改为纯本地\n\n"
        "### 资产\n"
        "- ClashOverlay.exe：Windows 覆盖层（免安装单文件）\n"
        "- ClashLabAnnotator.apk：手机战图标注器（Android 7+）\n"
        "- clashlab_annotated_20261126.zip：阵型标注/真实战图/压测数据\n\n"
        "> 非官方工具，与 Supercell 无关；请自行评估 ToS 风险。")
FILES = [
    ("ClashOverlay.exe", os.path.join(BASE, "dist", "ClashOverlay.exe")),
    ("ClashLabAnnotator.apk", os.path.join(BASE, "dist", "ClashLabAnnotator.apk")),
    ("clashlab_annotated_20261126.zip", os.path.join(BASE, "out", "backup", "clashlab_annotated_20261126.zip")),
]
def req(url, method="GET", data=None, ctype="application/json"):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "clashlab-release", "Accept": "application/vnd.github+json"}
    if data is not None: h["Content-Type"] = ctype
    r = urllib.request.Request(url, data=data, method=method, headers=h)
    with urllib.request.urlopen(r, timeout=900) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8", "ignore"))
rel = None
_, rels = req(API + "/repos/%s/releases?per_page=30" % REPO)
for x in rels:
    if x.get("tag_name") == TAG: rel = x; break
if rel is None:
    st, rel = req(API + "/repos/%s/releases" % REPO, "POST",
                  json.dumps({"tag_name": TAG, "name": NAME, "body": BODY,
                              "draft": False, "prerelease": False}).encode())
    print("created", st, rel["id"], flush=True)
else:
    print("exists", rel["id"], flush=True)
rid = rel["id"]
have = {a["name"]: a for a in rel.get("assets") or []}
for name, path in FILES:
    if name in have:
        print("skip existing", name, have[name]["size"], flush=True); continue
    size = os.path.getsize(path)
    print("upload", name, size, flush=True)
    with open(path, "rb") as f: body = f.read()
    st, art = req(UP + "/repos/%s/releases/%d/assets?name=%s" % (REPO, rid, urllib.parse.quote(name)),
                  "POST", body, "application/octet-stream")
    print("  ->", st, art.get("size"), flush=True)
_, rel2 = req(API + "/repos/%s/releases/%d" % (REPO, rid))
for a in rel2.get("assets") or []:
    print("ASSET", a["name"], a["size"], a["state"], a["browser_download_url"])
