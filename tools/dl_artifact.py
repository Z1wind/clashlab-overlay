# -*- coding: utf-8 -*-
import json, os, sys, urllib.request, urllib.error
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOKEN = os.environ["GH_TOKEN"]; REPO = "Z1wind/clashlab-overlay"; API = "https://api.github.com"
def gh_json(u):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
    return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60).read().decode())
runs = gh_json(API + "/repos/%s/actions/runs?per_page=15" % REPO)["workflow_runs"]
run = next(r for r in runs if r["name"] == "build-apk" and r["conclusion"] == "success")
arts = gh_json(API + "/repos/%s/actions/runs/%d/artifacts" % (REPO, run["id"]))["artifacts"]
a = arts[0]
print("run", run["id"], "| artifact", a["name"], a["size_in_bytes"])
for accept in ("application/zip", "application/octet-stream", None):
    try:
        h = {"Authorization": "token " + TOKEN, "User-Agent": "c"}
        if accept: h["Accept"] = accept
        req = urllib.request.Request(a["archive_download_url"], headers=h)
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read()
        print(accept, "-> HTTP", r.status, "bytes", len(data))
        open(os.path.join(r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out", "ci_artifact.zip"), "wb").write(data)
        break
    except urllib.error.HTTPError as e:
        print(accept, "-> HTTP", e.code, e.read()[:120])
    except Exception as e:
        print(accept, "-> ERR", str(e)[:120])
