# -*- coding: utf-8 -*-
"""更新 Release 资产：删除同名旧资产 → 重新上传 zip / SHA256SUMS。"""
import json, os, time, urllib.error, urllib.parse, urllib.request
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
TOKEN = os.environ["GH_TOKEN"]
REPO = "https://api.github.com/repos/Z1wind/clashlab-overlay"


def call(method, url, payload=None, raw=None, retries=3, timeout=600):
    headers = {"Authorization": "token " + TOKEN, "User-Agent": "clashlab", "Accept": "application/vnd.github+json"}
    data = None
    if payload is not None:
        data = json.dumps(payload).encode(); headers["Content-Type"] = "application/json"
    elif raw is not None:
        data = raw; headers["Content-Type"] = "application/octet-stream"
    last = None
    for attempt in range(retries):
        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read().decode("utf-8", "ignore")
                return json.loads(body) if body else {}
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "ignore"); last = "HTTP %s %s" % (e.code, body[:200])
            if e.code in (403, 429, 500, 502, 503, 504):
                time.sleep(3 * (attempt + 1)); continue
            raise RuntimeError(last)
    raise RuntimeError(last)


rel = call("GET", REPO + "/releases/tags/v0.1.0")
print("release:", rel["tag_name"], flush=True)
upload_base = rel["upload_url"].split("{")[0]
for fn in ("ClashLab_open_source_v0.1.0.zip", "SHA256SUMS.txt"):
    for a in rel["assets"]:
        if a["name"] == fn:
            call("DELETE", REPO + "/releases/assets/" + str(a["id"]))
            print("deleted old:", fn, flush=True)
    p = os.path.join(BASE, "out", "release", fn)
    raw = open(p, "rb").read()
    print("uploading", fn, len(raw), "B ...", flush=True)
    j = call("POST", upload_base + "?name=" + urllib.parse.quote(fn), raw=raw)
    print("  asset:", j.get("name"), j.get("size"), "B state=", j.get("state"), flush=True)
print("DONE", flush=True)
