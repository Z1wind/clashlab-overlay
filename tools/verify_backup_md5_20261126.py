# -*- coding: utf-8 -*-
import base64, hashlib, json, os, urllib.request, urllib.parse, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOKEN = os.environ["GH_TOKEN"]; REPO = "Z1wind/clashlab-overlay"; API = "https://api.github.com"
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
def get(u):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
    with urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))
for p in ("docs/STATUS.md", "README.md"):
    local = open(os.path.join(BASE, p), "rb").read()
    rb = base64.b64decode(get(API + "/repos/%s/contents/" % REPO + urllib.parse.quote(p))["content"].replace("\n", ""))
    print(p, len(local), "match=", hashlib.md5(local).hexdigest() == hashlib.md5(rb).hexdigest(), hashlib.md5(local).hexdigest())
