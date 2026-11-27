# -*- coding: utf-8 -*-
"""门控阈值扫描：候选数量/conf 分布 + 3 档可视化。"""
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
TH = [0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]
print("%-8s %-8s %-10s %-10s" % ("threshold", "items", "gated", "max_conf"))
rows = []
for thr in TH:
    r = ac.candidates(img_p, quad, max_n=60, gate_only=True, gate_threshold=thr)
    items = r.get("items") or []
    gated = sum((r.get("gated_counts") or {}).values())
    mx = max([i.get("gate_conf", 0) for i in items], default=0)
    rows.append((thr, len(items), gated, mx))
    print("%-8.2f %-8d %-10d %-10.4f" % (thr, len(items), gated, mx))
# 三档可视化
for thr, tag in ((0.60, "t060"), (0.75, "t075"), (0.85, "t085")):
    r = ac.candidates(img_p, quad, max_n=60, gate_only=True, gate_threshold=thr)
    vis = img0.copy()
    for i, it in enumerate(r.get("items") or []):
        x, y = it["tile"]; s = it["size"]
        pts = np.array([cal.tile_to_px(x,y), cal.tile_to_px(x+s,y), cal.tile_to_px(x+s,y+s), cal.tile_to_px(x,y+s)], np.int32)
        cv2.polylines(vis, [pts], True, (255, 220, 0), 2)
    cv2.putText(vis, "thr=%.2f items=%d" % (thr, len(r.get("items") or [])), (12, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 220, 255), 2)
    out = os.path.join(BASE, "out", "live", "gate_sweep_%s.png" % tag)
    cv2.imencode(".png", vis)[1].tofile(out)
    print("saved", out)
