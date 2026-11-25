# -*- coding: utf-8 -*-
import base64, hashlib, json, os, urllib.parse, urllib.request
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
TOKEN = os.environ["GH_TOKEN"]
REPO = "https://api.github.com/repos/Z1wind/clashlab-overlay"

def get(url):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))

for p in ("clashlab/topdown.py", "clashlab/topdown_cli.py", "tests/test_topdown.py",
          "docs/screenshots/topdown.png", "README.md", "docs/教程.md"):
    local = open(os.path.join(BASE, p), "rb").read()
    rem = get(REPO + "/contents/" + urllib.parse.quote(p))
    rb = base64.b64decode(rem["content"].replace("\n", ""))
    print("%-32s local=%6d remote=%6d match=%s" % (p, len(local), len(rb),
          hashlib.md5(local).hexdigest() == hashlib.md5(rb).hexdigest()))
runs = get(REPO + "/actions/runs?per_page=2")
for w in runs["workflow_runs"]:
    print("run:", w["head_sha"][:8], w["status"], w["conclusion"])
