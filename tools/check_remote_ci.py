# -*- coding: utf-8 -*-
"""无鉴权检查公开仓库：CI 工作流是否已补上、topics/描述、文件清单。"""
import base64, hashlib, json, os, urllib.request, urllib.parse
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
REPO = "https://api.github.com/repos/Z1wind/clashlab-overlay"

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "clashlab-check", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))

repo = get(REPO)
print("repo:", repo["full_name"], "| topics:", repo.get("topics") or "[]", "| desc:", (repo.get("description") or "")[:60])
c = get(REPO + "/commits?per_page=5")
print("commits:", len(c), "head:", c[0]["sha"][:10], c[0]["commit"]["message"][:50])
tree = get(REPO + "/git/trees/main?recursive=1")
blobs = [t for t in tree["tree"] if t["type"] == "blob"]
print("blobs:", len(blobs))
paths = {t["path"] for t in blobs}
for p in (".github/workflows/ci.yml", "docs/TUTORIAL_en.md", "README.en.md", "ATTRIBUTIONS.md"):
    print(("OK   " if p in paths else "MISS ") + p)
# 若 CI 存在，比对内容
if ".github/workflows/ci.yml" in paths:
    local = open(os.path.join(BASE, ".github", "workflows", "ci.yml"), "rb").read()
    remote = get(REPO + "/contents/" + urllib.parse.quote(".github/workflows/ci.yml"))
    rb = base64.b64decode(remote["content"].replace("\n", ""))
    print("ci.yml local=%d B remote=%d B md5match=%s" % (len(local), len(rb),
          hashlib.md5(local).hexdigest() == hashlib.md5(rb).hexdigest()))
    print("--- remote ci.yml ---")
    print(rb.decode("utf-8", "replace"))
