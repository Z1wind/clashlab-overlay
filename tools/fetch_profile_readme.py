# -*- coding: utf-8 -*-
import base64, hashlib, json, os, urllib.request
TOKEN = os.environ["GH_TOKEN"]; API = "https://api.github.com"
def get(u):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
    with urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))
c = get(API + "/repos/Z1wind/Z1wind/contents/README.md")
raw = base64.b64decode(c["content"].replace("\n", ""))
p = os.path.join(os.environ.get("TEMP", "."), "profile_readme.md")
open(p, "wb").write(raw)
print("saved:", p, os.path.getsize(p), "B")
print("local md5:", hashlib.md5(raw).hexdigest())
print("remote sha:", c["sha"][:12])
commit = get(API + "/repos/Z1wind/Z1wind/commits?per_page=1")[0]
print("commit:", commit["sha"][:10], commit["commit"]["committer"]["date"])
