# -*- coding: utf-8 -*-
import json, os, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOKEN = os.environ["GH_TOKEN"]
def gh(u):
    h = {"Authorization": "token " + TOKEN, "User-Agent": "c", "Accept": "application/vnd.github+json"}
    return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=60).read().decode())
try:
    items = gh("https://api.github.com/repos/Z1wind/clashlab-overlay/contents/android/assets/img")
    print("remote img count:", len(items))
    for it in items[:3]:
        print(" ", it["name"], it["size"])
except Exception as e:
    print("img dir err:", str(e)[:120])
# 检查 .gitignore 是否忽略
try:
    gi = gh("https://api.github.com/repos/Z1wind/clashlab-overlay/contents/.gitignore")
    import base64
    print(base64.b64decode(gi["content"]).decode("utf-8", "replace")[:500])
except Exception as e:
    print("gitignore err:", str(e)[:100])
