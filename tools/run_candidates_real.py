# -*- coding: utf-8 -*-
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
from clashlab import auto_candidates as ac
from clashlab.geo import Calib
import cv2, numpy as np
img_p = os.path.join(BASE, "out", "live", "enemy_scout_live.png")
quad = [[640,52],[1120,352],[640,652],[178,352]]
print("available:", ac.available())
r = ac.candidates(img_p, quad, max_n=30)
print("ok:", r.get("ok"), "| items:", len(r.get("items") or []), "| before dedupe:", r.get("total_before_dedupe"), "| err:", r.get("error"))
for it in (r.get("items") or [])[:12]:
    print(" ", it)
img = cv2.imdecode(np.fromfile(img_p, np.uint8), cv2.IMREAD_COLOR)
cal = Calib.from_quad(np.asarray(quad, np.float32), n=44)
for i, it in enumerate(r.get("items") or []):
    x, y = it["tile"]; s = it["size"]
    pts = np.array([cal.tile_to_px(x, y), cal.tile_to_px(x+s, y), cal.tile_to_px(x+s, y+s), cal.tile_to_px(x, y+s)], np.int32)
    cv2.polylines(img, [pts], True, (255, 220, 0), 2)
    p = cal.tile_to_px(x+s/2, y+s/2)
    cv2.putText(img, "%d:%s" % (i+1, it["type"][:10]), (int(p[0])-20, int(p[1])), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 220, 255), 1)
cv2.imencode(".png", img)[1].tofile(os.path.join(BASE, "out", "live", "candidates_real.png"))
print("saved candidates_real.png")
