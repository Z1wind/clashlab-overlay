# -*- coding: utf-8 -*-
"""一键导航到联机匹配：战斗 -> 搜索对手 -> 等侦察界面 -> OCR 敌方 -> API。全程后台日志。"""
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
    subprocess.run([ADB, "-s", "emulator-5554", "shell", "screencap", "-p", "/sdcard/_p_%s.png" % tag], capture_output=True, timeout=25)
    local = os.path.join(OUT, "_p_%s.png" % tag)
    subprocess.run([ADB, "-s", "emulator-5554", "pull", "/sdcard/_p_%s.png" % tag, local], capture_output=True, timeout=25)
    return cv2.imdecode(np.fromfile(local, np.uint8), cv2.IMREAD_COLOR)

def tap(x, y, wait=2.0):
    subprocess.run([ADB, "-s", "emulator-5554", "shell", "input", "tap", str(int(x)), str(int(y))], capture_output=True, timeout=20)
    time.sleep(wait)

def find_text(img, keyword):
    res, _ = ENGINE(img)
    best = None
    for box, text, score in (res or []):
        if keyword in str(text):
            xs = [p[0] for p in box]; ys = [p[1] for p in box]
            cx, cy = sum(xs)/4, sum(ys)/4
            if best is None or float(score) > best[2]:
                best = (cx, cy, float(score), str(text))
    return best

img = shot("home0")
print("home frame", img.shape, flush=True)
for attempt in range(2):
    b = find_text(img, "战斗")
    if b:
        print("tap 战斗 at", b[:3], flush=True); tap(b[0], b[1], 2.5)
    img = shot("menu%d" % attempt)
    s = find_text(img, "搜索对手")
    if not s:
        print("no search button; OCR texts:", [t for _, t, _ in (ENGINE(img)[0] or [])][:20], flush=True)
        break
    print("tap 搜索对手 at", s[:3], flush=True); tap(s[0], s[1], 3.0)
    hit = None
    for i in range(25):
        time.sleep(3)
        img = shot("m%d_%d" % (attempt, i))
        got = ocr_screen.read_opponent(img)
        lines = [l["text"] for l in got["lines"]]
        name, clan = got.get("name"), got.get("clan")
        atk = find_text(img, "进攻")
        print("[%d.%d] top=%s attack_btn=%s" % (attempt, i, lines, bool(atk)), flush=True)
        if name and len(name) >= 3 and name.lower() not in SELF and any(ch.isalpha() for ch in name) and atk:
            hit = (got, img)
            break
    if hit:
        got, img = hit
        cv2.imencode(".png", img)[1].tofile(os.path.join(OUT, "enemy_scout_live.png"))
        res = cocapi.resolve_opponent(got.get("name"), got.get("clan"), fresh=True, ocr_level=got.get("level"))
        p = res.get("player") or {}
        payload = {"ocr": got, "api": res, "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
        json.dump(payload, open(os.path.join(OUT, "enemy_scout_live.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("[HIT]", p.get("name"), p.get("tag"), "TH", p.get("th"), "ambiguous:", res.get("ambiguous"), flush=True)
        break
    print("no enemy found this attempt", flush=True)
print("nav done", flush=True)
