# -*- coding: utf-8 -*-
import base64, hashlib, json, os, urllib.request
TOKEN = os.environ["GH_TOKEN"]; REPO = "https://api.github.com/repos/Z1wind/clashlab-overlay"
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
def get(u):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
    with urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))
print("--- remote head ---")
for c in get(REPO + "/commits?per_page=2"):
    print(c["sha"][:8], c["commit"]["message"].splitlines()[0][:90])
print("--- runs ---")
for w in get(REPO + "/actions/runs?per_page=2")["workflow_runs"]:
    print(w["created_at"][:16], w["head_sha"][:8], w["status"], w["conclusion"])
print("--- md5 ---")
for p in ("clashlab/overlay/giant_arrow_diagram.py", "knowledge/tactics.json", "docs/TACTICS.md",
          "tests/test_giant_arrow_optimizer.py", "tests/test_tesla_tactics.py", "CHANGELOG.md", "README.md"):
    local = open(os.path.join(BASE, p), "rb").read()
    rb = base64.b64decode(get(REPO + "/contents/" + urllib.parse.quote(p))["content"].replace("\n", ""))
    print("%-42s %6d B match=%s md5=%s" % (p, len(local), hashlib.md5(local).hexdigest() == hashlib.md5(rb).hexdigest(), hashlib.md5(local).hexdigest()))
