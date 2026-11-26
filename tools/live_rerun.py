# -*- coding: utf-8 -*-
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat")
import numpy as np, cv2
from clashlab import ocr_screen, cocapi
img = cv2.imdecode(np.fromfile(r"out\live\enemy_live_frame.png", np.uint8), cv2.IMREAD_COLOR)
game = img[30:, :, :]
got = ocr_screen.read_opponent(game)
print("ocr:", {k: got.get(k) for k in ("level", "name", "clan")})
print("lines:", [l["text"] for l in got["lines"]])
res = cocapi.resolve_opponent(got.get("name"), got.get("clan"), fresh=True, ocr_level=got.get("level"))
p = res.get("player") or {}
print("player:", p.get("name"), p.get("tag"), "TH", p.get("th"), "| clan:", (p.get("clan") or {}).get("name"))
payload = {"ocr": got, "api": res, "fetched_at": __import__("time").strftime("%Y-%m-%dT%H:%M:%S")}
json.dump(payload, open(r"out\live\enemy_live2.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("saved out/live/enemy_live2.json")
