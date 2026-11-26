# -*- coding: utf-8 -*-
import json, os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat")
import numpy as np, cv2
from clashlab import ocr_screen, cocapi
ADB = r"E:\leidian\LDPlayer9\adb.exe"
OUT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\live"

def shot(tag):
    subprocess.run([ADB, "-s", "emulator-5554", "shell", "screencap", "-p", "/sdcard/_a_%s.png" % tag], capture_output=True, timeout=25)
    local = os.path.join(OUT, "_a_%s.png" % tag)
    subprocess.run([ADB, "-s", "emulator-5554", "pull", "/sdcard/_a_%s.png" % tag, local], capture_output=True, timeout=25)
    return cv2.imdecode(np.fromfile(local, np.uint8), cv2.IMREAD_COLOR)

def tap(x, y, wait=2.0):
    subprocess.run([ADB, "-s", "emulator-5554", "shell", "input", "tap", str(int(x)), str(int(y))], capture_output=True, timeout=20)
    time.sleep(wait)

tap(1217, 60, 2.5)   # 关闭军队面板，露出敌方基地
img = shot("enemybase")
cv2.imencode(".png", img)[1].tofile(os.path.join(OUT, "enemy_base_scout.png"))
got = ocr_screen.read_opponent(img)
print("ocr:", {k: got.get(k) for k in ("level", "name", "clan", "tag")})
print("lines:", [l["text"] for l in got.get("lines")])
res = None
if got.get("name") or got.get("tag"):
    res = cocapi.resolve_opponent(got.get("name") or got.get("tag"), got.get("clan"), fresh=True, ocr_level=got.get("level"))
    p = res.get("player") or {}
    print("player:", p.get("name"), p.get("tag"), "TH", p.get("th"), "| ambiguous:", res.get("ambiguous"))
    payload = {"ocr": got, "api": res, "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    json.dump(payload, open(os.path.join(OUT, "enemy_multiplayer.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("saved enemy_multiplayer.json")
