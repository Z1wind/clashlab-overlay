# -*- coding: utf-8 -*-
import base64, hashlib, json, os, urllib.parse, urllib.request, time
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
TOKEN = os.environ["GH_TOKEN"]; REPO = "https://api.github.com/repos/Z1wind/clashlab-overlay"
def get(u):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
    with urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))
p = "docs/RECOG_RESULTS.md"
local = open(os.path.join(BASE, p), "rb").read()
rb = base64.b64decode(get(REPO + "/contents/" + urllib.parse.quote(p))["content"].replace("\n", ""))
print("%s local=%d remote=%d match=%s" % (p, len(local), len(rb), hashlib.md5(local).hexdigest() == hashlib.md5(rb).hexdigest()))
print("result json:", os.path.getsize(os.path.join(BASE, "out", "recog", "train_from_annotations.json")), "B")
time.sleep(8)
runs = get(REPO + "/actions/runs?per_page=2")
for w in runs["workflow_runs"]:
    print("run:", w["head_sha"][:8], w["status"], w["conclusion"])
