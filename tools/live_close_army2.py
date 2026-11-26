# -*- coding: utf-8 -*-
import json, os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat")
import numpy as np, cv2
from rapidocr_onnxruntime import RapidOCR
from clashlab import ocr_screen, cocapi
ADB = r"E:\leidian\LDPlayer9\adb.exe"
OUT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\live"
ENGINE = RapidOCR()

def shot(tag):
    subprocess.run([ADB, "-s", "emulator-5554", "shell", "screencap", "-p", "/sdcard/_x_%s.png" % tag], capture_output=True, timeout=25)
    local = os.path.join(OUT, "_x_%s.png" % tag)
    subprocess.run([ADB, "-s", "emulator-5554", "pull", "/sdcard/_x_%s.png" % tag, local], capture_output=True, timeout=25)
    return cv2.imdecode(np.fromfile(local, np.uint8), cv2.IMREAD_COLOR)

def tap(x, y, wait=2.5):
    subprocess.run([ADB, "-s", "emulator-5554", "shell", "input", "tap", str(int(x)), str(int(y))], capture_output=True, timeout=20)
    time.sleep(wait)

img = shot("before_close")
res, _ = ENGINE(img)
print("texts:", [t for _, t, _ in (res or [])][:15], flush=True)
tap(1217, 60)          # 关闭我的军队面板
img = shot("enemy")
cv2.imencode(".png", img)[1].tofile(os.path.join(OUT, "enemy_scout_view.png"))
got = ocr_screen.read_opponent(img)
print("ocr:", {k: got.get(k) for k in ("level", "name", "clan", "tag")}, flush=True)
print("lines:", [l["text"] for l in got["lines"]], flush=True)
res2, _ = ENGINE(img)
print("full texts:", [t for _, t, _ in (res2 or [])][:20], flush=True)
if got.get("name") or got.get("tag"):
    r = cocapi.resolve_opponent(got.get("name") or got.get("tag"), got.get("clan"), fresh=True, ocr_level=got.get("level"))
    p = r.get("player") or {}
    print("player:", p.get("name"), p.get("tag"), "TH", p.get("th"), "ambiguous:", r.get("ambiguous"), flush=True)
    json.dump({"ocr": got, "api": r, "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S")},
              open(os.path.join(OUT, "enemy_scout_view.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
