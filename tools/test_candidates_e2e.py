# -*- coding: utf-8 -*-
import json, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
B = "http://127.0.0.1:8765"
quad = [[640,52],[1120,352],[640,652],[178,352]]
req = urllib.request.Request(B + "/candidates", data=json.dumps({"quad": quad, "max_n": 12}).encode(),
                             headers={"Content-Type": "application/json"})
j = json.loads(urllib.request.urlopen(req, timeout=120).read().decode())
print("ok:", j.get("ok"), "| items:", len(j.get("items") or []), "| err:", j.get("error"))
for it in (j.get("items") or [])[:5]:
    print("  ", it)
