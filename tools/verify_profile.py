# -*- coding: utf-8 -*-
import base64, hashlib, json, os, urllib.request, urllib.error
TOKEN = os.environ["GH_TOKEN"]; API = "https://api.github.com"
def call(method, url, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
    if data is not None: h["Content-Type"] = "application/json"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data, method=method, headers=h), timeout=60) as r:
            b = r.read().decode("utf-8", "ignore"); return r.status, (json.loads(b) if b else {})
    except urllib.error.HTTPError as e:
        return e.code, {"_body": e.read().decode("utf-8", "ignore")[:200]}
st, repo = call("GET", API + "/repos/Z1wind/Z1wind")
print("repo:", st, repo.get("full_name"), "| default:", repo.get("default_branch"))
st, c = call("GET", API + "/repos/Z1wind/Z1wind/contents/README.md")
raw = base64.b64decode(c["content"].replace("\n", "")) if st == 200 else b""
print("readme:", st, len(raw), "B md5:", hashlib.md5(raw).hexdigest()[:12])
print("has email1:", "1808016780@qq.com" in raw.decode("utf-8", "ignore"))
print("has discord:", "discord.gg/HVh8KdNM" in raw.decode("utf-8", "ignore"))
print("has X:", "standkeepmoving" in raw.decode("utf-8", "ignore"))
st, r = call("PATCH", API + "/user", {"bio": "太原理工大学材料科学在读 | 课余做电脑程序研究 & 游戏玩法优化 | ClashLab 作者"})
print("bio update:", st, (r.get("bio") or r.get("_body"))[:80])
