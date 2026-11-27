# -*- coding: utf-8 -*-
import json, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
B = "http://127.0.0.1:8765"
quad = [[640,52],[1120,352],[640,652],[178,352]]
for recall, thr in ((False, 0.85), (True, 0.70), (True, 0.55)):
    req = urllib.request.Request(B + "/candidates",
        data=json.dumps({"quad": quad, "max_n": 80, "gate_only": True, "gate_threshold": thr, "recall": recall}).encode(),
        headers={"Content-Type": "application/json"})
    j = json.loads(urllib.request.urlopen(req, timeout=120).read().decode())
    print("recall=%s thr=%.2f -> ok=%s items=%d" % (recall, thr, j.get("ok"), len(j.get("items") or [])))
