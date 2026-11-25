# -*- coding: utf-8 -*-
"""本地 vs 远端 md5 对照（精简/双语改动文件）。"""
import base64, hashlib, json, os, urllib.parse, urllib.request
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
TOKEN = os.environ["GH_TOKEN"]
REPO = "https://api.github.com/repos/Z1wind/clashlab-overlay"

def get(url):
    req = urllib.request.Request(url, headers={"Authorization": "token " + TOKEN, "User-Agent": "v",
                                               "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))

def md5(b): return hashlib.md5(b).hexdigest().upper()

paths = ["README.md", "README.en.md", "LICENSE", "ATTRIBUTIONS.md", "PACKAGING.md", "CHANGELOG.md",
         "docs/教程.md", "docs/TUTORIAL_en.md", "clashlab/layout_score.py",
         "clashlab/defense_findings.py", "clashlab/overlay/score_card.py"]
ok = 0
for p in paths:
    local = open(os.path.join(BASE, p), "rb").read()
    remote = get(REPO + "/contents/" + urllib.parse.quote(p))
    rb = base64.b64decode(remote["content"].replace("\n", ""))
    same = md5(local) == md5(rb)
    ok += same
    print("%-34s local=%6d B %s | remote=%6d B %s | match=%s" % (p, len(local), md5(local)[:8], len(rb), md5(rb)[:8], same))
print("MATCH %d/%d" % (ok, len(paths)))
r = get(REPO)
print("repo:", r["full_name"], "| commits:", len(get(REPO + "/commits?per_page=5")))
