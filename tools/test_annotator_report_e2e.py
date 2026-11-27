# -*- coding: utf-8 -*-
import json, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
lay = {"name": "annotator_e2e", "grid": 44,
       "buildings": [{"type": "town-hall", "tile": [20, 20]},
                     {"type": "inferno-tower", "tile": [16, 16]},
                     {"type": "eagle-artillery", "tile": [24, 16]}],
       "walls": []}
req = urllib.request.Request("http://127.0.0.1:8765/battle-report",
                             data=json.dumps({"name": "annotator_e2e", "layout": lay, "th": 15}).encode(),
                             headers={"Content-Type": "application/json"})
j = json.loads(urllib.request.urlopen(req, timeout=60).read().decode())
print(json.dumps({k: j.get(k) for k in ("ok", "path", "bytes", "grade", "score", "error")}, ensure_ascii=False))
