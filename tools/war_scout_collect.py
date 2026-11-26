# -*- coding: utf-8 -*-
"""战争地图批量采集：检测侦察屏（有「进攻!」且左上名字非自己），每座存 PNG+JSON。"""
import hashlib, json, os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat")
import numpy as np, cv2
from rapidocr_onnxruntime import RapidOCR
from clashlab import ocr_screen, cocapi
ADB = r"E:\leidian\LDPlayer9\adb.exe"
OUT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\live\scouts"
os.makedirs(OUT, exist_ok=True)
E = RapidOCR()
SELF = ("z1wind", "zlwind", "pnimiz", "小砸锤")
seen = set()

def shot(tag):
    subprocess.run([ADB, "-s", "emulator-5554", "shell", "screencap", "-p", "/sdcard/w_%s.png" % tag], capture_output=True, timeout=25)
    p = os.path.join(OUT, "_w_%s.png" % tag)
    subprocess.run([ADB, "-s", "emulator-5554", "pull", "/sdcard/w_%s.png" % tag, p], capture_output=True, timeout=25)
    return cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)

def has_attack(img):
    res, _ = E(img)
    return any("进攻" in str(t) for _, t, _ in (res or []))

start = time.time()
n = 0
while time.time() - start < 180:
    try:
        img = shot("w")
    except Exception:
        time.sleep(3); continue
    if img is None:
        time.sleep(3); continue
    if not has_attack(img):
        time.sleep(3); continue
    got = ocr_screen.read_opponent(img)
    name = (got.get("name") or "").strip()
    clan = (got.get("clan") or "").strip()
    if not name or name.lower() in SELF or name in ("进攻",):
        time.sleep(3); continue
    key = hashlib.md5((name + "|" + clan).encode("utf-8")).hexdigest()[:10]
    if key in seen:
        time.sleep(3); continue
    seen.add(key)
    n += 1
    png = os.path.join(OUT, "scout_%02d_%s.png" % (n, key))
    cv2.imencode(".png", img)[1].tofile(png)
    try:
        api = cocapi.resolve_opponent(name, clan, fresh=True, ocr_level=got.get("level"))
    except Exception as e:
        api = {"error": str(e)[:80]}
    json.dump({"ocr": got, "api": api, "png": png, "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S")},
              open(os.path.join(OUT, "scout_%02d_%s.json" % (n, key)), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    p = (api.get("player") or {}) if isinstance(api, dict) else {}
    print("[capture %d] %s / %s -> %s TH%s" % (n, name, clan, p.get("tag"), p.get("th")), flush=True)
    time.sleep(3)
print("watcher done, captured:", n, flush=True)
