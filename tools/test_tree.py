# -*- coding: utf-8 -*-
import json, urllib.request, urllib.error, base64, os
T = os.environ.get("GH_TOKEN", "")
API = "https://api.github.com"
REPO = API + "/repos/Z1wind/clashlab-overlay"

def call(method, url, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Authorization": "token " + T, "User-Agent": "t", "Accept": "application/vnd.github+json",
                                          "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return {"_err": e.code, "_body": e.read().decode()[:300]}

b1 = call("POST", REPO + "/git/blobs", {"content": base64.b64encode(b"a").decode(), "encoding": "base64"})
b2 = call("POST", REPO + "/git/blobs", {"content": base64.b64encode(b"b").decode(), "encoding": "base64"})
print("blobs:", b1.get("sha"), b2.get("sha"))
print("2-entry tree:", call("POST", REPO + "/git/trees", {"tree": [
    {"path": "a/x.txt", "mode": "100644", "type": "blob", "sha": b1["sha"]},
    {"path": "b/y.txt", "mode": "100644", "type": "blob", "sha": b2["sha"]},
]}))
big = {"tree": [{"path": "f%d.txt" % i, "mode": "100644", "type": "blob", "sha": b1["sha"]} for i in range(1023)]}
r = call("POST", REPO + "/git/trees", big)
print("1023-entry tree:", {k: r[k] for k in r if k != "tree"} if "_err" in r else r.get("sha"))
