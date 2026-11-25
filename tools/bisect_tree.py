# -*- coding: utf-8 -*-
"""二分找最导致 tree 404 的条目。"""
import json, os, subprocess, hashlib, urllib.error, urllib.request
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN = os.environ["GH_TOKEN"]
REPO = "https://api.github.com/repos/Z1wind/clashlab-overlay"
cache = json.load(open(os.path.join(BASE, "out", "release", "blob_cache.json"), encoding="utf-8"))
git = os.path.join(os.environ.get("TEMP", ""), "gitportable", "mingit", "cmd", "git.exe")
out = subprocess.run([git, "-c", "core.quotepath=false", "ls-files", "-z"], cwd=BASE, capture_output=True, check=True).stdout
files = [os.fsdecode(x) for x in out.split(b"\x00") if x]


def ent(rel):
    with open(os.path.join(BASE, rel), "rb") as f:
        raw = f.read()
    sha = cache[rel + "@" + hashlib.sha1(raw).hexdigest()]
    return {"path": rel, "mode": "100644", "type": "blob", "sha": sha}


def ok(entries):
    data = json.dumps({"tree": entries}).encode()
    req = urllib.request.Request(REPO + "/git/trees", data=data, method="POST",
                                 headers={"Authorization": "token " + TOKEN, "User-Agent": "t",
                                          "Accept": "application/vnd.github+json", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return True
    except urllib.error.HTTPError as e:
        e.read()
        return False


cur = files
while len(cur) > 1:
    half = len(cur) // 2
    first = cur[:half]
    if ok([ent(f) for f in first]):
        cur = cur[half:]
    else:
        cur = first
    print("candidate group size:", len(cur), flush=True)
bad = cur[0]
print("BAD PATH:", repr(bad), flush=True)
print("single ok?:", ok([ent(bad)]))
print("bytes:", bad.encode("utf-8", "replace").hex()[:400])
