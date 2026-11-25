# -*- coding: utf-8 -*-
"""本地 vs 远端一致性校验：内容 md5 对照 + release 资产字节数对照。"""
import base64, hashlib, json, os, urllib.request
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
TOKEN = os.environ["GH_TOKEN"]
REPO = "https://api.github.com/repos/Z1wind/clashlab-overlay"


def get(url):
    req = urllib.request.Request(url, headers={"Authorization": "token " + TOKEN, "User-Agent": "v",
                                               "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))


def md5(b):
    return hashlib.md5(b).hexdigest().upper()


for path in ("README.md", "LICENSE", "clashlab/layout_score.py", "docs/教程.md"):
    local = open(os.path.join(BASE, path), "rb").read()
    remote = get(REPO + "/contents/" + urllib.parse.quote(path))
    rb = base64.b64decode(remote["content"].replace("\n", ""))
    print("%-28s local_md5=%s local=%d B | remote_md5=%s remote=%d B | match=%s" % (
        path, md5(local), len(local), md5(rb), len(rb), md5(local) == md5(rb)))

rel = get(REPO + "/releases/tags/v0.1.0")
for a in rel["assets"]:
    lp = os.path.join(BASE, "out", "release", a["name"])
    lsize = os.path.getsize(lp) if os.path.exists(lp) else -1
    print("%-38s remote=%d B local=%d B match=%s" % (a["name"], a["size"], lsize, a["size"] == lsize))
