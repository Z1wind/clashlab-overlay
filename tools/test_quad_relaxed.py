# -*- coding: utf-8 -*-
import json, urllib.request
def req(method, url, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    r = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(r, timeout=10) as resp:
            return resp.status, resp.read().decode("utf-8", "ignore")[:200]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")[:200]
base = "http://127.0.0.1:8765"
print("GET /:", req("GET", base + "/")[0])
print("POST outside quad:", req("POST", base + "/api/quad?th=th16&id=01",
      {"quad": [[1338.1, -180.9], [2150, 480], [1180, 1180], [500, 480]]}))
print("GET quad:", req("GET", base + "/api/quad?th=th16&id=01")[1][:120])
print("DELETE:", req("DELETE", base + "/api/quad?th=th16&id=01"))
