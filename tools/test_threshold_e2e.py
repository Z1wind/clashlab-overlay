# -*- coding: utf-8 -*-
import json, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
B = "http://127.0.0.1:8765"
quad = [[640,52],[1120,352],[640,652],[178,352]]
for thr in (0.60, 0.75, 0.85):
    req = urllib.request.Request(B + "/candidates",
        data=json.dumps({"quad": quad, "max_n": 60, "gate_only": True, "gate_threshold": thr}).encode(),
        headers={"Content-Type": "application/json"})
    j = json.loads(urllib.request.urlopen(req, timeout=120).read().decode())
    print("thr=%.2f ok=%s items=%d gated=%s" % (thr, j.get("ok"), len(j.get("items") or []), j.get("gated_counts")))
