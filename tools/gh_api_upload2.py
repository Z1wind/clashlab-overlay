# -*- coding: utf-8 -*-
"""通过 GitHub API 把本地 git 跟踪文件导入仓库（带 blob 缓存，避免重复上传）。"""
import argparse, base64, concurrent.futures as cf, hashlib, json, os, subprocess, sys, time, urllib.error, urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://api.github.com"
CACHE = os.path.join(BASE, "out", "release", "blob_cache.json")


def git(*args):
    for p in (os.path.join(os.environ.get("TEMP", ""), "gitportable", "mingit", "cmd", "git.exe"), "git"):
        try:
            return subprocess.run([p, "-c", "core.quotepath=false"] + list(args), cwd=BASE,
                                  capture_output=True, check=True).stdout
        except FileNotFoundError:
            continue
    raise SystemExit("git not found")


def api(method, url, token, payload=None, timeout=120, retries=6):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Authorization": "token " + token, "User-Agent": "clashlab-uploader",
               "Accept": "application/vnd.github+json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    last = None
    for attempt in range(retries):
        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8", "ignore")
                return json.loads(body) if body else {}
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "ignore")
            last = "HTTP %s %s" % (e.code, body[:200])
            if e.code in (403, 429, 500, 502, 503, 504):
                time.sleep(min(60, 3 * (2 ** attempt)))
                continue
            raise RuntimeError(last)
        except Exception as e:
            last = repr(e)[:200]
            time.sleep(min(30, 2 * (2 ** attempt)))
    raise RuntimeError(last)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--token", required=True)
    ap.add_argument("--owner", default="Z1wind")
    ap.add_argument("--repo", default="clashlab-overlay")
    ap.add_argument("--branch", default="main")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    repo_api = "%s/repos/%s/%s" % (API, a.owner, a.repo)
    cache = {}
    if os.path.exists(CACHE):
        try:
            cache = json.load(open(CACHE, encoding="utf-8"))
        except Exception:
            cache = {}

    out = git("ls-files", "-z")
    files = [os.fsdecode(x) for x in out.split(b"\x00") if x]
    # .github/workflows/* 需要 PAT 带 workflow scope，否则 GitHub 用 404 拒绝；
    # 先跳过（本地仓库仍有该文件），用户可在网页端手工添加或换带 workflow 权限的 token。
    skipped = [f for f in files if f.startswith(".github/workflows/")]
    files = [f for f in files if not f.startswith(".github/workflows/")]
    print("files:", len(files), "skipped(workflow):", len(skipped), flush=True)

    items = []
    for rel in files:
        p = os.path.join(BASE, rel)
        with open(p, "rb") as f:
            raw = f.read()
        key = rel + "@" + hashlib.sha1(raw).hexdigest()
        items.append((rel, key, base64.b64encode(raw).decode("ascii")))

    shas = [cache.get(it[1]) for it in items]
    todo = [i for i, s in enumerate(shas) if not s]
    print("cached:", len(shas) - len(todo), "to upload:", len(todo), flush=True)
    errs = []

    def worker(i):
        rel, key, b64 = items[i]
        for attempt in range(4):
            try:
                r = api("POST", repo_api + "/git/blobs", a.token, {"content": b64, "encoding": "base64"})
                return i, r["sha"], key
            except Exception as e:
                if attempt == 3:
                    errs.append("%s :: %s" % (rel, str(e)[:120]))
                    return i, None, key
                time.sleep(2 * (attempt + 1))
        return i, None, key

    done = 0
    with cf.ThreadPoolExecutor(max_workers=a.workers) as ex:
        for i, sha, key in ex.map(worker, todo):
            done += 1
            shas[i] = sha
            if sha:
                cache[key] = sha
            if done % 100 == 0:
                json.dump(cache, open(CACHE, "w", encoding="utf-8"), indent=0)
                print("blobs %d/%d (fail=%d)" % (done, len(todo), len(errs)), flush=True)
    json.dump(cache, open(CACHE, "w", encoding="utf-8"), indent=0)
    bad = [i for i, s in enumerate(shas) if not s]
    print("missing blobs:", len(bad), flush=True)
    if bad:
        for e in errs[:5]:
            print("  err:", e, flush=True)
        raise SystemExit(1)

    entries = [{"path": items[i][0], "mode": "100644", "type": "blob", "sha": shas[i]} for i in range(len(items))]
    parent = api("GET", repo_api + "/git/ref/heads/" + a.branch, a.token)
    print("parent:", parent["object"]["sha"], flush=True)
    tree = api("POST", repo_api + "/git/trees", a.token, {"tree": entries})
    print("tree:", tree["sha"], "entries:", len(entries), flush=True)
    commit = api("POST", repo_api + "/git/commits", a.token,
                 {"message": "chore: initial open-source release v0.1.0 (imported via API)",
                  "tree": tree["sha"], "parents": [parent["object"]["sha"]]})
    print("commit:", commit["sha"], flush=True)
    ref = api("PATCH", repo_api + "/git/refs/heads/" + a.branch, a.token, {"sha": commit["sha"], "force": True})
    print("ref:", ref["ref"], "->", ref["object"]["sha"], flush=True)
    v = api("GET", repo_api + "/git/trees/" + a.branch + "?recursive=1", a.token)
    print("remote entries:", len(v.get("tree", [])), flush=True)
    print("DONE", flush=True)


main()
