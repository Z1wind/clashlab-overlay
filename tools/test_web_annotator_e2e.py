# -*- coding: utf-8 -*-
import json, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
B = "http://127.0.0.1:8766"
with urllib.request.urlopen(B + "/", timeout=20) as r:
    html = r.read().decode("utf-8", "ignore")
print("page HTTP", r.status, "len", len(html), "| has 出报告:", "出报告" in html, "| has wall mode:", "画墙模式" in html)
lay = {"name":"webtest","grid":44,"quad":[[640,52],[1120,352],[640,652],[178,352]],
       "buildings":[{"type":"town-hall","tile":[20,20]},{"type":"air-defense","tile":[18,18]},
                    {"type":"air-sweeper","tile":[20,10]},{"type":"gold-storage","tile":[16,24]}],
       "walls":[[10,10],[34,10],[34,34],[10,34],[10,10]]}
req = urllib.request.Request(B + "/save", data=json.dumps(lay).encode(), headers={"Content-Type":"application/json"})
with urllib.request.urlopen(req, timeout=30) as r:
    print("save:", r.read().decode()[:120])
req = urllib.request.Request(B + "/report", data=json.dumps({"name":"webtest"}).encode(), headers={"Content-Type":"application/json"})
with urllib.request.urlopen(req, timeout=120) as r:
    j = json.loads(r.read().decode())
print("report ok:", j.get("ok"), "| summary head:", (j.get("summary") or "")[:160].replace("\n"," "))
