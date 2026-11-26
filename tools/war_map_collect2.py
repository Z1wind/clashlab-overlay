# -*- coding: utf-8 -*-
"""战争地图采集 v2：按画面 dHash 去重，多点几个敌方基地就多收几套真实战图。"""
import json, os, subprocess, sys, time
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

def shot(tag):
    subprocess.run([ADB, "-s", "emulator-5554", "shell", "screencap", "-p", "/sdcard/v_%s.png" % tag], capture_output=True, timeout=25)
    p = os.path.join(OUT, "_v_%s.png" % tag)
    subprocess.run([ADB, "-s", "emulator-5554", "pull", "/sdcard/v_%s.png" % tag, p], capture_output=True, timeout=25)
    return cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)

def dhash(img):
    g = cv2.cvtColor(img[80:640, 200:1080], cv2.COLOR_BGR2GRAY)
    g = cv2.resize(g, (16, 16), interpolation=cv2.INTER_AREA)
    bits = (g[:, 1:] > g[:, :-1]).flatten()
    return "".join("1" if b else "0" for b in bits)

def hamming(a, b):
    return sum(1 for x, y in zip(a, b) if x != y)

def has_attack(img):
    res, _ = E(img)
    return any("进攻" in str(t) for _, t, _ in (res or []))

seen, n = [], 0
start = time.time()
while time.time() - start < 300:
    try:
        img = shot("v")
    except Exception:
        time.sleep(2.5); continue
    if img is None or not has_attack(img):
        time.sleep(2.5); continue
    h = dhash(img)
    if any(hamming(h, s) < 8 for s in seen):
        time.sleep(2.5); continue
    got = ocr_screen.read_opponent(img)
    name = (got.get("name") or "").strip()
    if not name or name.lower() in SELF:
        time.sleep(2.5); continue
    seen.append(h); n += 1
    png = os.path.join(OUT, "map_%02d.png" % n)
    cv2.imencode(".png", img)[1].tofile(png)
    try:
        api = cocapi.resolve_opponent(name, got.get("clan"), fresh=True, ocr_level=got.get("level"))
    except Exception as e:
        api = {"error": str(e)[:100]}
    p = (api.get("player") or {}) if isinstance(api, dict) else {}
    json.dump({"ocr": got, "api": api, "png": png, "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S")},
              open(os.path.join(OUT, "map_%02d.json" % n), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("[map %d] %s / %s -> %s TH%s" % (n, name, got.get("clan"), p.get("tag"), p.get("th")), flush=True)
    time.sleep(2.0)
print("collector v2 done, maps:", n, flush=True)
