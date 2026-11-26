# -*- coding: utf-8 -*-
import json, os, urllib.request
base = "http://127.0.0.1:8781"
items = json.load(urllib.request.urlopen(base + "/api/list"))["items"]
first = items[0]["file"]
payload = json.dumps({"file": first, "quad": [[100, 100], [2000, 500], [1000, 1100], [100, 600]]}).encode()
r = urllib.request.Request(base + "/api/save", data=payload, method="POST", headers={"Content-Type": "application/json"})
try:
    with urllib.request.urlopen(r, timeout=10) as resp:
        print("POST valid:", resp.status, resp.read().decode()[:200])
except urllib.error.HTTPError as e:
    print("POST valid FAILED:", e.code, e.read().decode()[:200])
# 清理测试标注
p = os.path.join(r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat", "out", "corners")
for fn in os.listdir(p):
    print("corner file:", fn)
    os.remove(os.path.join(p, fn))
print("items:", len(items))
