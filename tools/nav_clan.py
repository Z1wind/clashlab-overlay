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
    subprocess.run([ADB, "-s", "emulator-5554", "shell", "screencap", "-p", "/sdcard/_c_%s.png" % tag], capture_output=True, timeout=25)
    local = os.path.join(OUT, "_c_%s.png" % tag)
    subprocess.run([ADB, "-s", "emulator-5554", "pull", "/sdcard/_c_%s.png" % tag, local], capture_output=True, timeout=25)
    return cv2.imdecode(np.fromfile(local, np.uint8), cv2.IMREAD_COLOR)

def tap(x, y, wait=2.5):
    subprocess.run([ADB, "-s", "emulator-5554", "shell", "input", "tap", str(int(x)), str(int(y))], capture_output=True, timeout=20)
    time.sleep(wait)

tap(55, 285)          # 左侧部落图标
img = shot("clan")
cv2.imencode(".png", img)[1].tofile(os.path.join(OUT, "clan_screen.png"))
res, _ = ENGINE(img)
for box, text, score in (res or [])[:35]:
    xs = [p[0] for p in box]; ys = [p[1] for p in box]
    print("%-16s (%.0f,%.0f) score=%.2f" % (str(text)[:16], sum(xs)/4, sum(ys)/4, float(score)))
