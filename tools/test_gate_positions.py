# -*- coding: utf-8 -*-
import json, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
B = "http://127.0.0.1:8765"
quad = [[640,52],[1120,352],[640,652],[178,352]]
req = urllib.request.Request(B + "/candidates", data=json.dumps({"quad": quad, "max_n": 40, "gate_only": True}).encode(),
                             headers={"Content-Type": "application/json"})
j = json.loads(urllib.request.urlopen(req, timeout=120).read().decode())
print("ok:", j.get("ok"), "| gate_only:", j.get("gate_only"), "| items:", len(j.get("items") or []),
      "| gated:", j.get("gated_counts"), "| err:", j.get("error"))
for it in (j.get("items") or [])[:6]:
    print("  ", it)
