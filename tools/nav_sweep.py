# -*- coding: utf-8 -*-
import os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat")
import numpy as np, cv2
from rapidocr_onnxruntime import RapidOCR
ADB = r"E:\leidian\LDPlayer9\adb.exe"
OUT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\live"
E = RapidOCR()

def shot(tag):
    subprocess.run([ADB, "-s", "emulator-5554", "shell", "screencap", "-p", "/sdcard/nav_%s.png" % tag], capture_output=True, timeout=25)
    p = os.path.join(OUT, "_nav_%s.png" % tag)
    subprocess.run([ADB, "-s", "emulator-5554", "pull", "/sdcard/nav_%s.png" % tag, p], capture_output=True, timeout=25)
    return cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)

def tap(x, y):
    subprocess.run([ADB, "-s", "emulator-5554", "shell", "input", "tap", str(x), str(y)], capture_output=True, timeout=20)
    time.sleep(1.4)

def texts(img):
    res, _ = E(img)
    return [str(t) for _, t, _ in (res or [])]

KEY = ("部落战", "战争地图", "成员", "部落", "进攻", "侦察")
for (x, y) in ((195, 607), (300, 607), (420, 607), (500, 607), (640, 607), (55, 285), (55, 345), (980, 607), (1070, 607)):
    tap(x, y)
    img = shot("t%d_%d" % (x, y))
    ts = texts(img)
    hit = [t for t in ts if any(k in t for k in KEY)]
    print("tap", (x, y), "->", ("HIT " + str(hit)) if hit else ts[:8], flush=True)
    if hit:
        cv2.imencode(".png", img)[1].tofile(os.path.join(OUT, "nav_hit_%d_%d.png" % (x, y)))
        break
    subprocess.run([ADB, "-s", "emulator-5554", "shell", "input", "keyevent", "4"], capture_output=True, timeout=20)
    time.sleep(1.2)
print("sweep done", flush=True)
