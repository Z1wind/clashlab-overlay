# -*- coding: utf-8 -*-
import base64, hashlib, json, os, urllib.request
TOKEN = os.environ["GH_TOKEN"]; API = "https://api.github.com"
def get(u):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
    with urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))
c = get(API + "/repos/Z1wind/Z1wind/contents/README.md")
raw = base64.b64decode(c["content"].replace("\n", ""))
txt = raw.decode("utf-8")
print("size:", len(raw), "B | md5:", hashlib.md5(raw).hexdigest()[:12])
print("有「材料科学与工程在读」:", "材料科学与工程在读" in txt)
print("有英文 Materials Science and Engineering:", "Materials Science and Engineering" in txt)
print("残留旧词「材料科学在读」:", "材料科学在读" in txt)
me = get(API + "/user")
print("bio:", (me.get("bio") or "").encode("ascii", "replace").decode())
