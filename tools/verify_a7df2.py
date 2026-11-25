# -*- coding: utf-8 -*-
import base64, hashlib, json, os, urllib.parse, urllib.request
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
TOKEN = os.environ["GH_TOKEN"]; REPO = "https://api.github.com/repos/Z1wind/clashlab-overlay"
def get(u):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
    with urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))
for p in ("docs/BASELINK_RESEARCH.md", "README.md"):
    full = os.path.join(BASE, p)
    local = open(full, "rb").read()
    st = os.stat(full)
    import datetime
    mt = datetime.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    rem = get(REPO + "/contents/" + urllib.parse.quote(p))
    rb = base64.b64decode(rem["content"].replace("\n", ""))
    print("%s\n  local : size=%d md5=%s mtime=%s\n  remote: size=%d md5=%s sha=%s\n  match=%s" % (
        p, len(local), hashlib.md5(local).hexdigest().upper(), mt,
        len(rb), hashlib.md5(rb).hexdigest().upper(), rem["sha"][:12],
        hashlib.md5(local).hexdigest() == hashlib.md5(rb).hexdigest()))
c = get(REPO + "/commits/a7df44f1")
print("commit a7df44f1 date:", c["commit"]["committer"]["date"], "| author:", c["commit"]["author"]["name"])
