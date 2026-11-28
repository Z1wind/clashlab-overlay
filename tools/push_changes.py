# -*- coding: utf-8 -*-
"""增量推送：只为变更文件创建 blob，基于远端当前 tree 生成新 tree -> commit -> 更新 main。"""
import base64, hashlib, json, os, subprocess, sys, time, urllib.error, urllib.request
urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))

BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
TOKEN = os.environ["GH_TOKEN"]
REPO = "https://api.github.com/repos/Z1wind/clashlab-overlay"
CACHE = os.path.join(BASE, "out", "release", "blob_cache.json")
_CANDIDATES = [
    os.path.join(os.environ.get("TEMP", ""), "mingit2", "cmd", "git.exe"),
    os.path.join(os.environ.get("TEMP", ""), "gitportable", "mingit", "cmd", "git.exe"),
    r"E:\Temp\mingit2\cmd\git.exe",
    r"C:\Program Files\Git\cmd\git.exe",
]
git = next((c for c in _CANDIDATES if os.path.exists(c)), _CANDIDATES[0])


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
                time.sleep(min(30, 2 ** attempt)); continue
            raise RuntimeError(last)
        except Exception as e:
            last = repr(e)[:200]; time.sleep(min(30, 2 ** attempt))
    raise RuntimeError(last)


cache = json.load(open(CACHE, encoding="utf-8"))
out = subprocess.run([git, "-c", "core.quotepath=false", "ls-files", "-z"], cwd=BASE, capture_output=True, check=True).stdout
files = [os.fsdecode(x) for x in out.split(b"\x00") if x and not x.startswith(b".github/workflows/")]
changed = []
for rel in files:
    with open(os.path.join(BASE, rel), "rb") as f:
        raw = f.read()
    key = rel + "@" + hashlib.sha1(raw).hexdigest()
    if key in cache:
        continue
    r = call("POST", REPO + "/git/blobs", {"content": base64.b64encode(raw).decode(), "encoding": "base64"})
    cache[key] = r["sha"]
    changed.append({"path": rel, "mode": "100644", "type": "blob", "sha": r["sha"]})
    print("new blob:", rel, flush=True)
json.dump(cache, open(CACHE, "w", encoding="utf-8"), indent=0)
print("changed files:", len(changed), flush=True)
if not changed:
    print("nothing to push"); sys.exit(0)

head = call("GET", REPO + "/git/ref/heads/main")
head_sha = head["object"]["sha"]
commit_info = call("GET", REPO + "/git/commits/" + head_sha)
tree = call("POST", REPO + "/git/trees", {"base_tree": commit_info["tree"]["sha"], "tree": changed})
print("tree:", tree["sha"], flush=True)
def _local_commit_message():
    try:
        r = subprocess.run([git, "log", "-1", "--pretty=%B"], cwd=BASE, capture_output=True, text=True)
        m = (r.stdout or "").strip()
        return m or "chore: sync workspace"
    except Exception:
        return "chore: sync workspace"


MSG = _local_commit_message()
print("commit message:", (MSG.splitlines() or [""])[0][:80], flush=True)
commit = call("POST", REPO + "/git/commits", {"message": MSG,
                                              "tree": tree["sha"], "parents": [head_sha]})
print("commit:", commit["sha"], flush=True)
ref = call("PATCH", REPO + "/git/refs/heads/main", {"sha": commit["sha"], "force": True})
print("ref:", ref["ref"], flush=True)
print("DONE", flush=True)
