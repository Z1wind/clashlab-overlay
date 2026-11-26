# -*- coding: utf-8 -*-
import json, os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat")
import numpy as np, cv2
from clashlab import ocr_screen, cocapi
ADB = r"E:\leidian\LDPlayer9\adb.exe"
OUT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\live"

def shot(tag):
    subprocess.run([ADB, "-s", "emulator-5554", "shell", "screencap", "-p", "/sdcard/_m_%s.png" % tag], capture_output=True, timeout=25)
    local = os.path.join(OUT, "_m_%s.png" % tag)
    subprocess.run([ADB, "-s", "emulator-5554", "pull", "/sdcard/_m_%s.png" % tag, local], capture_output=True, timeout=25)
    return cv2.imdecode(np.fromfile(local, np.uint8), cv2.IMREAD_COLOR)

def tap(x, y, wait=2.0):
    subprocess.run([ADB, "-s", "emulator-5554", "shell", "input", "tap", str(int(x)), str(int(y))], capture_output=True, timeout=20)
    time.sleep(wait)

tap(196, 520, 3.0)   # 常规战「搜索对手」
print("tapped search", flush=True)
for i in range(20):
    time.sleep(3)
    img = shot("match%d" % i)
    if img is None: continue
    got = ocr_screen.read_opponent(img)
    lines = [l["text"] for l in got.get("lines") or []]
    print("[%d] ocr=%s" % (i, lines), flush=True)
    name, clan = got.get("name"), got.get("clan")
    if name and clan and len(name) >= 3:
        try:
            res = cocapi.resolve_opponent(name, clan, fresh=True, ocr_level=got.get("level"))
        except Exception as e:
            print("api fail", str(e)[:80], flush=True); continue
        p = res.get("player") or {}
        if p.get("tag"):
            payload = {"ocr": got, "api": res, "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
            json.dump(payload, open(os.path.join(OUT, "enemy_multiplayer.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            cv2.imencode(".png", img)[1].tofile(os.path.join(OUT, "enemy_multiplayer_frame.png"))
            print("[HIT]", p.get("name"), p.get("tag"), "TH", p.get("th"), "| ambiguous:", res.get("ambiguous"), flush=True)
            break
print("done", flush=True)
