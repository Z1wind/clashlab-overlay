# -*- coding: utf-8 -*-
import json, os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat")
import numpy as np, cv2
from clashlab import ocr_screen, cocapi
ADB = r"E:\leidian\LDPlayer9\adb.exe"
OUT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\live"
subprocess.run([ADB, "-s", "emulator-5554", "shell", "screencap", "-p", "/sdcard/scout_now.png"], capture_output=True, timeout=25)
local = os.path.join(OUT, "enemy_scout_live.png")
subprocess.run([ADB, "-s", "emulator-5554", "pull", "/sdcard/scout_now.png", local], capture_output=True, timeout=25)
img = cv2.imdecode(np.fromfile(local, np.uint8), cv2.IMREAD_COLOR)
print("frame:", None if img is None else img.shape)
if img is not None:
    got = ocr_screen.read_opponent(img)
    print("ocr:", {k: got.get(k) for k in ("level", "name", "clan", "tag")})
    print("lines:", [l["text"] for l in got["lines"]])
    if got.get("name") or got.get("tag"):
        res = cocapi.resolve_opponent(got.get("name") or got.get("tag"), got.get("clan"), fresh=True, ocr_level=got.get("level"))
        p = res.get("player") or {}
        print("player:", p.get("name"), p.get("tag"), "TH", p.get("th"), "| ambiguous:", res.get("ambiguous"))
        print("clan:", res.get("clan"))
        json.dump({"ocr": got, "api": res, "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S")},
                  open(os.path.join(OUT, "enemy_scout_live.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("saved enemy_scout_live.json")
