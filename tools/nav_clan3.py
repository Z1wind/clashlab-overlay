# -*- coding: utf-8 -*-
import os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat")
import numpy as np, cv2
from rapidocr_onnxruntime import RapidOCR
ADB = r"E:\leidian\LDPlayer9\adb.exe"
OUT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\live"
ENGINE = RapidOCR()

def shot(tag):
    subprocess.run([ADB, "-s", "emulator-5554", "shell", "screencap", "-p", "/sdcard/_g_%s.png" % tag], capture_output=True, timeout=25)
    local = os.path.join(OUT, "_g_%s.png" % tag)
    subprocess.run([ADB, "-s", "emulator-5554", "pull", "/sdcard/_g_%s.png" % tag, local], capture_output=True, timeout=25)
    return cv2.imdecode(np.fromfile(local, np.uint8), cv2.IMREAD_COLOR)

def tap(x, y, wait=2.2):
    subprocess.run([ADB, "-s", "emulator-5554", "shell", "input", "tap", str(int(x)), str(int(y))], capture_output=True, timeout=20)
    time.sleep(wait)

def texts(img):
    res, _ = ENGINE(img)
    out = []
    for box, text, score in (res or []):
        xs = [p[0] for p in box]; ys = [p[1] for p in box]
        out.append((str(text), int(sum(xs)/4), int(sum(ys)/4)))
    return out

tap(70, 350)   # 部落图标（按裁剪坐标修正）
img = shot("clan")
cv2.imencode(".png", img)[1].tofile(os.path.join(OUT, "clan_screen2.png"))
for t in texts(img)[:30]:
    print(t, flush=True)
