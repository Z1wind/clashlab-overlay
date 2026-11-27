# -*- coding: utf-8 -*-
import json, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = "https://api.clashk.ing"
CAND = ["/openapi.json", "/swagger.json", "/v2/openapi.json", "/v2/swagger.json", "/docs/openapi.json",
        "/api/openapi.json", "/v3/openapi.json", "/openapi.yaml"]
def get(path, raw=False):
    try:
        with urllib.request.urlopen(urllib.request.Request(BASE + path, headers={"User-Agent": "clashlab"}), timeout=20) as r:
            data = r.read()
            return r.status, r.headers.get("Content-Type"), data
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Content-Type"), e.read(200)
    except Exception as e:
        return "ERR", "", str(e)[:100].encode()
for p in CAND:
    st, ct, data = get(p)
    print(p, "->", st, ct, len(data), data[:60])
# 从 /docs HTML 找 spec 线索
st, ct, html = get("/docs")
txt = html.decode("utf-8", "ignore")
import re
for m in re.findall(r'["\']([^"\']*(?:openapi|swagger|spec|json)[^"\']*)["\']', txt)[:10]:
    print("docs ref:", m)
