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
SELF = ("z1wind", "pnimiz", "pn!miz", "小砸锤")

def shot(tag):
    subprocess.run([ADB, "-s", "emulator-5554", "shell", "screencap", "-p", "/sdcard/_q_%s.png" % tag], capture_output=True, timeout=25)
    local = os.path.join(OUT, "_q_%s.png" % tag)
    subprocess.run([ADB, "-s", "emulator-5554", "pull", "/sdcard/_q_%s.png" % tag, local], capture_output=True, timeout=25)
    return cv2.imdecode(np.fromfile(local, np.uint8), cv2.IMREAD_COLOR)

def tap(x, y, wait=2.5):
    subprocess.run([ADB, "-s", "emulator-5554", "shell", "input", "tap", str(int(x)), str(int(y))], capture_output=True, timeout=20)
    time.sleep(wait)

def has_text(img, keyword):
    res, _ = ENGINE(img)
    return any(keyword in str(t) for _, t, _ in (res or []))

tap(80, 650)                      # 战斗
img = shot("menu")
print("menu has 搜索对手:", has_text(img, "搜索对手"), flush=True)
cv2.imencode(".png", img)[1].tofile(os.path.join(OUT, "nav_menu2.png"))
if has_text(img, "搜索对手"):
    tap(196, 520, 3.0)            # 搜索对手（常规战）
for i in range(30):
    time.sleep(3)
    img = shot("scout%d" % i)
    got = ocr_screen.read_opponent(img)
    lines = [l["text"] for l in got["lines"]]
    atk = has_text(img, "进攻")
    print("[%d] top=%s attack=%s" % (i, lines, atk), flush=True)
    name = got.get("name")
    if name and len(name) >= 3 and name.lower() not in SELF and atk:
        cv2.imencode(".png", img)[1].tofile(os.path.join(OUT, "enemy_scout_live.png"))
        res = cocapi.resolve_opponent(name, got.get("clan"), fresh=True, ocr_level=got.get("level"))
        p = res.get("player") or {}
        payload = {"ocr": got, "api": res, "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
        json.dump(payload, open(os.path.join(OUT, "enemy_scout_live.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("[HIT]", p.get("name"), p.get("tag"), "TH", p.get("th"), "ambiguous:", res.get("ambiguous"), flush=True)
        break
print("done", flush=True)
