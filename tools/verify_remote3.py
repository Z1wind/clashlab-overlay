# -*- coding: utf-8 -*-
import base64, hashlib, json, os, urllib.parse, urllib.request
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
TOKEN = os.environ["GH_TOKEN"]
REPO = "https://api.github.com/repos/Z1wind/clashlab-overlay"

def get(url):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))

paths = ["README.md", "README.en.md", "CHANGELOG.md", "CODE_OF_CONDUCT.md", "run_overlay.py",
         "overlay_exe_main.py", "clashlab/overlay/runtime.py", ".github/PULL_REQUEST_TEMPLATE.md",
         ".github/ISSUE_TEMPLATE/bug_report.yml"]
ok = 0
for p in paths:
    local = open(os.path.join(BASE, p), "rb").read()
    rem = get(REPO + "/contents/" + urllib.parse.quote(p))
    rb = base64.b64decode(rem["content"].replace("\n", ""))
    same = hashlib.md5(local).hexdigest() == hashlib.md5(rb).hexdigest()
    ok += same
    print("%-40s local=%5d B remote=%5d B match=%s" % (p, len(local), len(rb), same))
print("MATCH %d/%d" % (ok, len(paths)))
runs = get(REPO + "/actions/runs?per_page=3")
for w in runs["workflow_runs"]:
    print("run:", w["head_sha"][:8], w["status"], w["conclusion"])
