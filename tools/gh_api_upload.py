# -*- coding: utf-8 -*-
"""通过 GitHub API 把本地 git 跟踪文件导入到空仓库（绕开 github.com DNS 劫持）。

用法（token 只作为参数，不写入任何文件）：
    python tools/gh_api_upload.py --token <PAT> [--owner Z1wind --repo clashlab-overlay]

流程：逐文件创建 blob（并发 3 + 403/429 退避重试）→ 建 tree → 建 commit（父=当前 main）→ 更新 ref。
"""
import argparse
import base64
import concurrent.futures as cf
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://api.github.com"


def git(*args):
    return subprocess.run(["git"] + list(args), cwd=BASE, capture_output=True, check=True).stdout


def find_git():
    for p in (os.path.join(os.environ.get("TEMP", ""), "gitportable", "mingit", "cmd", "git.exe"), "git"):
        try:
            subprocess.run([p, "--version"], capture_output=True, check=True)
            return p
        except Exception:
            continue
    raise SystemExit("git not found")


GIT = find_git()


def api(method, url, token, payload=None, timeout=60, retries=6):
    data = None
    headers = {"Authorization": "token " + token, "User-Agent": "clashlab-uploader",
               "Accept": "application/vnd.github+json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
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
        except Exception as e:  # 网络
            last = repr(e)[:200]
            time.sleep(min(30, 2 * (2 ** attempt)))
    raise RuntimeError(last)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--token", required=True)
    ap.add_argument("--owner", default="Z1wind")
    ap.add_argument("--repo", default="clashlab-overlay")
    ap.add_argument("--branch", default="main")
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    repo_api = "%s/repos/%s/%s" % (API, a.owner, a.repo)

    out = subprocess.run([GIT, "-c", "core.quotepath=false", "-c", "core.longpaths=true", "ls-files", "-z"],
                         cwd=BASE, capture_output=True, check=True).stdout
    files = [os.fsdecode(x) for x in out.split(b"\x00") if x]
    print("files:", len(files), flush=True)

    data = []
    for rel in files:
        p = os.path.join(BASE, rel)
        with open(p, "rb") as f:
            data.append((rel, base64.b64encode(f.read()).decode("ascii")))
    print("loaded bytes ok", flush=True)

    shas = [None] * len(data)
    errors = []

    def worker(i):
        rel, b64 = data[i]
        for attempt in range(5):
            try:
                r = api("POST", repo_api + "/git/blobs", a.token, {"content": b64, "encoding": "base64"}, retries=4)
                return i, r["sha"]
            except Exception as e:
                if attempt == 4:
                    errors.append("%s :: %s" % (rel, str(e)[:120]))
                    return i, None
                time.sleep(2 * (attempt + 1))
        return i, None

    done = 0
    with cf.ThreadPoolExecutor(max_workers=a.workers) as ex:
        for i, sha in ex.map(worker, range(len(data))):
            shas[i] = sha
            done += 1
            if done % 100 == 0:
                print("blobs %d/%d (errors=%d)" % (done, len(data), len(errors)), flush=True)
    bad = [x for x in shas if not x]
    print("blobs done, failed:", len(bad), flush=True)
    if bad:
        for e in errors[:5]:
            print("  err:", e, flush=True)
        raise SystemExit("blob failures; rerun later (already-uploaded shas are reused by GitHub)")

    entries = [{"path": d[0], "mode": "100644", "type": "blob", "sha": shas[i]} for i, d in enumerate(data)]
    parent = api("GET", repo_api + "/git/ref/heads/" + a.branch, a.token)
    parent_sha = parent["object"]["sha"]
    print("parent:", parent_sha, flush=True)
    tree = api("POST", repo_api + "/git/trees", a.token, {"tree": entries})
    print("tree:", tree["sha"], flush=True)
    commit = api("POST", repo_api + "/git/commits", a.token,
                 {"message": "chore: initial open-source release v0.1.0 (imported via API)",
                  "tree": tree["sha"], "parents": [parent_sha]})
    print("commit:", commit["sha"], flush=True)
    ref = api("PATCH", repo_api + "/git/refs/heads/" + a.branch, a.token, {"sha": commit["sha"], "force": True})
    print("ref:", ref["ref"], "->", ref["object"]["sha"], flush=True)
    v = api("GET", repo_api + "/git/trees/" + a.branch + "?recursive=1", a.token)
    print("remote entries:", len(v.get("tree", [])), flush=True)
    print("DONE", flush=True)


main()
