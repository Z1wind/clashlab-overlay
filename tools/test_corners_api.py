# -*- coding: utf-8 -*-
import json, urllib.request
def req(method, url, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    r = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(r, timeout=10) as resp:
            return resp.status, resp.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")[:200]
base = "http://127.0.0.1:8781"
print("GET /:", req("GET", base + "/")[0])
print("GET /api/list:", req("GET", base + "/api/list")[1][:300])
print("POST bad quad:", req("POST", base + "/api/save", {"file": "x.jpg", "quad": [[1,2]]}))
