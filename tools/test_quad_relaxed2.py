# -*- coding: utf-8 -*-
import json, urllib.request, urllib.error
def req(method, url, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    r = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(r, timeout=10) as resp:
            return resp.status, resp.read().decode("utf-8", "ignore")[:260]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")[:260]
base = "http://127.0.0.1:8765"
quad = [[1338.1, -180.9], [2150, 480], [1180, 1180], [500, 480]]
print("POST outside-corner quad:", req("POST", base + "/api/quad", {"th": "th16", "id": "01", "quad": quad}))
print("GET quad after:", req("GET", base + "/api/quad?th=th16&id=01")[1][:180])
print("DELETE:", req("DELETE", base + "/api/quad?th=th16&id=01")[0])
print("GET quad after delete source:", "layout" in req("GET", base + "/api/quad?th=th16&id=01")[1])
