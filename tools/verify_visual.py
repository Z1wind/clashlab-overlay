# -*- coding: utf-8 -*-
import base64, hashlib, json, os, time, urllib.parse, urllib.request
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
TOKEN = os.environ["GH_TOKEN"]; REPO = "https://api.github.com/repos/Z1wind/clashlab-overlay"
def get(u):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
    with urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))
for p in ("clashlab/overlay/draw.py", "clashlab/overlay/runtime.py", "clashlab/topdown.py",
          "tests/test_topdown.py", "docs/screenshots/panel_visual.png",
          "docs/screenshots/topdown_visual.png", "docs/screenshots/hud_marks.png"):
    local = open(os.path.join(BASE, p), "rb").read()
    rb = base64.b64decode(get(REPO + "/contents/" + urllib.parse.quote(p))["content"].replace("\n", ""))
    print("%-34s local=%7d remote=%7d match=%s" % (p, len(local), len(rb), hashlib.md5(local).hexdigest() == hashlib.md5(rb).hexdigest()))
runs = get(REPO + "/actions/runs?per_page=2")
for w in runs["workflow_runs"]:
    print("CI:", w["head_sha"][:8], w["status"], w["conclusion"])
