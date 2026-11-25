# -*- coding: utf-8 -*-
"""用「增量 tree」方式提交：按目录递归创建子树，避免单次 tree 过大（GitHub 422 timeout）。"""
import json, os, subprocess, hashlib, sys, time, urllib.error, urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://api.github.com"
TOKEN = os.environ["GH_TOKEN"]
REPO = API + "/repos/Z1wind/clashlab-overlay"
cache = json.load(open(os.path.join(BASE, "out", "release", "blob_cache.json"), encoding="utf-8"))
git = os.path.join(os.environ.get("TEMP", ""), "gitportable", "mingit", "cmd", "git.exe")


def call(method, url, payload=None, retries=5):
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {"Authorization": "token " + TOKEN, "User-Agent": "clashlab", "Accept": "application/vnd.github+json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    last = None
    for attempt in range(retries):
        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                body = r.read().decode("utf-8", "ignore")
                return json.loads(body) if body else {}
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "ignore")
            last = "HTTP %s %s" % (e.code, body[:200])
            if e.code in (403, 429, 500, 502, 503, 504):
                time.sleep(min(30, 2 ** attempt))
                continue
            raise RuntimeError(last)
        except Exception as e:
            last = repr(e)[:200]
            time.sleep(min(30, 2 ** attempt))
    raise RuntimeError(last)


out = subprocess.run([git, "-c", "core.quotepath=false", "ls-files", "-z"], cwd=BASE, capture_output=True, check=True).stdout
files = [os.fsdecode(x) for x in out.split(b"\x00") if x and not x.startswith(b".github/workflows/")]
blob_sha = {}
for rel in files:
    with open(os.path.join(BASE, rel), "rb") as f:
        raw = f.read()
    key = rel + "@" + hashlib.sha1(raw).hexdigest()
    if key not in cache:
        raise SystemExit("missing blob in cache: " + rel)
    blob_sha[rel] = cache[key]
print("files:", len(files), flush=True)

# 目录结构：{dirname: {"files": {name: sha}, "dirs": {...}}}
root_node = {"files": {}, "dirs": {}}
for rel in files:
    parts = rel.split("/")
    node = root_node
    for d in parts[:-1]:
        node = node["dirs"].setdefault(d, {"files": {}, "dirs": {}})
    node["files"][parts[-1]] = blob_sha[rel]

created = 0


def build(node, path):
    global created
    entries = []
    for name, sha in sorted(node["files"].items()):
        entries.append({"path": name, "mode": "100644", "type": "blob", "sha": sha})
    for dname, child in sorted(node["dirs"].items()):
        sha = build(child, path + "/" + dname if path else dname)
        entries.append({"path": dname, "mode": "040000", "type": "tree", "sha": sha})
    if not entries:
        return None
    r = call("POST", REPO + "/git/trees", {"tree": entries})
    created += 1
    if created % 10 == 0:
        print("  subtrees:", created, "last:", path, flush=True)
    return r["sha"]


root_sha = build(root_node, "")
print("root tree:", root_sha, "subtrees:", created, flush=True)
parent = call("GET", REPO + "/git/ref/heads/main")
print("parent:", parent["object"]["sha"], flush=True)
commit = call("POST", REPO + "/git/commits",
              {"message": "chore: initial open-source release v0.1.0 (incremental tree import)",
               "tree": root_sha, "parents": [parent["object"]["sha"]]})
print("commit:", commit["sha"], flush=True)
ref = call("PATCH", REPO + "/git/refs/heads/main", {"sha": commit["sha"], "force": True})
print("ref:", ref["ref"], "->", ref["object"]["sha"], flush=True)
v = call("GET", REPO + "/git/trees/main?recursive=1")
print("remote entries:", len(v.get("tree", [])), flush=True)
print("DONE", flush=True)
