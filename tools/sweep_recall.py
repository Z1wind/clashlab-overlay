# -*- coding: utf-8 -*-
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab import auto_candidates as ac
from clashlab.geo import Calib
import cv2, numpy as np
img_p = os.path.join(BASE, "out", "live", "enemy_scout_live.png")
quad = [[640,52],[1120,352],[640,652],[178,352]]
img0 = cv2.imdecode(np.fromfile(img_p, np.uint8), cv2.IMREAD_COLOR)
cal = Calib.from_quad(np.asarray(quad, np.float32), n=44)
print("%-8s %-8s %-8s" % ("thr", "normal", "recall"))
for thr in (0.50, 0.55, 0.60, 0.70, 0.85):
    a = ac.candidates(img_p, quad, max_n=60, gate_only=True, gate_threshold=thr)
    b = ac.candidates(img_p, quad, max_n=60, gate_only=True, gate_threshold=thr, recall=True)
    print("%-8.2f %-8d %-8d" % (thr, len(a.get("items") or []), len(b.get("items") or [])))
for thr, tag in ((0.55, "recall055"), (0.70, "recall070")):
    r = ac.candidates(img_p, quad, max_n=80, gate_only=True, gate_threshold=thr, recall=True)
    vis = img0.copy()
    for it in (r.get("items") or []):
        x, y = it["tile"]; s = it["size"]
        pts = np.array([cal.tile_to_px(x,y), cal.tile_to_px(x+s,y), cal.tile_to_px(x+s,y+s), cal.tile_to_px(x,y+s)], np.int32)
        cv2.polylines(vis, [pts], True, (0, 200, 255), 1)
    cv2.putText(vis, "recall thr=%.2f items=%d" % (thr, len(r.get("items") or [])), (12, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 220, 255), 2)
    out = os.path.join(BASE, "out", "live", "gate_%s.png" % tag)
    cv2.imencode(".png", vis)[1].tofile(out)
    print("saved", out)
