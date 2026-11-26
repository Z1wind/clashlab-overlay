# -*- coding: utf-8 -*-
"""战争地图采集 v3：按 API tag（或名字+部落）去重，玩家逐个点基地就一套一套收。"""
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
    subprocess.run([ADB, "-s", "emulator-5554", "shell", "screencap", "-p", "/sdcard/u_%s.png" % tag], capture_output=True, timeout=25)
    p = os.path.join(OUT, "_u_%s.png" % tag)
    subprocess.run([ADB, "-s", "emulator-5554", "pull", "/sdcard/u_%s.png" % tag, p], capture_output=True, timeout=25)
    return cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)

def has_attack(img):
    res, _ = E(img)
    return any("进攻" in str(t) for _, t, _ in (res or []))

def norm(s):
    return "".join(ch for ch in str(s or "").lower() if ch.isalnum())

seen, n = set(), 0
start = time.time()
while time.time() - start < 480:
    try:
        img = shot("u")
    except Exception:
        time.sleep(2.5); continue
    if img is None or not has_attack(img):
        time.sleep(2.5); continue
    got = ocr_screen.read_opponent(img)
    name = (got.get("name") or "").strip()
    clan = (got.get("clan") or "").strip()
    if not name or name.lower() in SELF:
        time.sleep(2.5); continue
    key = "raw:" + norm(name) + "|" + norm(clan)
    if key in seen:
        time.sleep(2.5); continue
    try:
        api = cocapi.resolve_opponent(name, clan, fresh=True, ocr_level=got.get("level"))
    except Exception as e:
        api = {"error": str(e)[:100]}
    p = (api.get("player") or {}) if isinstance(api, dict) else {}
    tag = (p.get("tag") or "").upper()
    real_key = tag if tag else key
    if real_key in seen:
        time.sleep(2.5); continue
    seen.add(key); seen.add(real_key); n += 1
    png = os.path.join(OUT, "war_%02d_%s.png" % (n, (tag or "unknown").lstrip("#")))
    cv2.imencode(".png", img)[1].tofile(png)
    row = {"n": n, "ocr": got, "api": api, "tag": tag, "th": p.get("th"), "png": png,
           "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    json.dump(row, open(os.path.join(OUT, "war_%02d.json" % n), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("[war %d] %s / %s -> %s TH%s" % (n, name, clan, tag, p.get("th")), flush=True)
    time.sleep(2.0)
print("collector v3 done, maps:", n, flush=True)
