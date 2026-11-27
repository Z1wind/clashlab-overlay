# -*- coding: utf-8 -*-
import json, sys, time, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
B = "http://127.0.0.1:8767"
for _ in range(10):
    try:
        with urllib.request.urlopen(B + "/", timeout=5) as r:
            html = r.read().decode("utf-8", "ignore"); break
    except Exception:
        time.sleep(1)
else:
    raise SystemExit("server not up")
print("page:", r.status, len(html), "| 箭线预览:", "箭线预览" in html, "| snap:", "function snap(" in html, "| arrow route call:", "/arrow" in html)
lay = {"name":"webtest2","grid":44,"quad":[[640,52],[1120,352],[640,652],[178,352]],
       "buildings":[{"type":"town-hall","tile":[20,20]},{"type":"air-defense","tile":[18,18]},
                    {"type":"air-sweeper","tile":[20,10]}],"walls":[]}
req = urllib.request.Request(B + "/save", data=json.dumps(lay).encode(), headers={"Content-Type":"application/json"})
print("save:", urllib.request.urlopen(req, timeout=20).read().decode()[:80])
req = urllib.request.Request(B + "/arrow", data=json.dumps({"name":"webtest2","from":[10,10],"to":[30,30]}).encode(),
                             headers={"Content-Type":"application/json"})
j = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
print("arrow ok:", j.get("ok"), "| hits:", j.get("hits"), "| summary:", j.get("summary"), "| score:", j.get("score"))
