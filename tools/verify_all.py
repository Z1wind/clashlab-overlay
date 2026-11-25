# -*- coding: utf-8 -*-
import base64, hashlib, json, os, urllib.parse, urllib.request
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
TOKEN = os.environ["GH_TOKEN"]
REPO = "https://api.github.com/repos/Z1wind/clashlab-overlay"
def get(u):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
    with urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))
paths = ["tools/annotate/start.py", "tools/annotate/index.html", "tools/annotate/README.md",
         "clashlab/wall_symmetry.py", "clashlab/baselink.py", "clashlab/recog_dataset.py",
         "README.md", "CONTRIBUTING.md", "tests/test_annotate.py"]
ok = 0
for p in paths:
    local = open(os.path.join(BASE, p), "rb").read()
    rem = get(REPO + "/contents/" + urllib.parse.quote(p))
    rb = base64.b64decode(rem["content"].replace("\n", ""))
    same = hashlib.md5(local).hexdigest() == hashlib.md5(rb).hexdigest()
    ok += same
    print("%-38s local=%7d remote=%7d match=%s" % (p, len(local), len(rb), same))
print("MATCH %d/%d" % (ok, len(paths)))
runs = get(REPO + "/actions/runs?per_page=3")
for w in runs["workflow_runs"]:
    print("run:", w["head_sha"][:8], w["status"], w["conclusion"])
