# -*- coding: utf-8 -*-
import base64, hashlib, json, os, urllib.request
TOKEN = os.environ["GH_TOKEN"]; API = "https://api.github.com"
def get(u):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
    with urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))
c = get(API + "/repos/Z1wind/Z1wind/contents/README.md")
raw = base64.b64decode(c["content"].replace("\n", ""))
print("profile README:", len(raw), "B md5", hashlib.md5(raw).hexdigest()[:12], "| sha", c["sha"][:10])
commit = get(API + "/repos/Z1wind/Z1wind/commits?per_page=1")[0]
print("profile commit:", commit["sha"][:10], commit["commit"]["committer"]["date"])
me = get(API + "/user")
print("bio len:", len(me.get("bio") or ""))
