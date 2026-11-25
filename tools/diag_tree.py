# -*- coding: utf-8 -*-
"""二分定位：GitHub tree 创建 404 是哪条路径引起的（复用 blob 缓存，不重复上传）。"""
import json, os, subprocess, sys, urllib.error, urllib.request
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://api.github.com"
TOKEN = os.environ["GH_TOKEN"]
REPO = API + "/repos/Z1wind/clashlab-overlay"
cache = json.load(open(os.path.join(BASE, "out", "release", "blob_cache.json"), encoding="utf-8"))
git = os.path.join(os.environ.get("TEMP", ""), "gitportable", "mingit", "cmd", "git.exe")
out = subprocess.run([git, "-c", "core.quotepath=false", "ls-files", "-z"], cwd=BASE, capture_output=True, check=True).stdout
files = [os.fsdecode(x) for x in out.split(b"\x00") if x]
import hashlib


def entry(rel):
    with open(os.path.join(BASE, rel), "rb") as f:
        raw = f.read()
    key = rel + "@" + hashlib.sha1(raw).hexdigest()
    sha = cache.get(key)
    return {"path": rel, "mode": "100644", "type": "blob", "sha": sha} if sha else None


def try_tree(entries):
    data = json.dumps({"tree": entries}).encode()
    req = urllib.request.Request(REPO + "/git/trees", data=data, method="POST",
                                 headers={"Authorization": "token " + TOKEN, "User-Agent": "t",
                                          "Accept": "application/vnd.github+json", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return 0, len(entries), r.read()[:80]
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")
        return e.code, len(entries), body[:120]


ents = [entry(f) for f in files]
missing = [f for f, e in zip(files, ents) if e is None]
print("files", len(files), "entries", len(ents), "cached_missing", len(missing))
ents = [e for e in ents if e]
print("try all:", try_tree(ents)[:2], flush=True)
half = len(ents) // 2
print("try first half:", try_tree(ents[:half])[:2], flush=True)
print("try second half:", try_tree(ents[half:])[:2], flush=True)
# 若两半都过，说明是总量问题：试 3/4
if True:
    q = len(ents) * 3 // 4
    print("try 3/4:", try_tree(ents[:q])[:2], flush=True)
