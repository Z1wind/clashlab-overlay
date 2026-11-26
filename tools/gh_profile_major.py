# -*- coding: utf-8 -*-
"""更新个人主页 README：专业改为「材料科学与工程」。"""
import base64, json, os, urllib.error, urllib.request
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
st, cur = call("GET", API + "/repos/Z1wind/Z1wind/contents/README.md")
raw = base64.b64decode(cur["content"].replace("\n", "")).decode("utf-8")
new = raw.replace("材料科学在读", "材料科学与工程在读").replace("Materials Science @", "Materials Science and Engineering @")
print("changed:", new != raw, "| old bytes", len(raw.encode()), "-> new", len(new.encode()))
payload = {"message": "Update major: Materials Science and Engineering", "content": base64.b64encode(new.encode()).decode(), "branch": "main", "sha": cur["sha"]}
st, r = call("PUT", API + "/repos/Z1wind/Z1wind/contents/README.md", payload)
print("put:", st, r.get("commit", {}).get("sha") or r.get("_body"))
st, r = call("PATCH", API + "/user", {"bio": "太原理工大学材料科学与工程在读 | 课余做电脑程序研究 & 游戏玩法优化 | ClashLab 作者"})
print("bio:", st)
