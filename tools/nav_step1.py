# -*- coding: utf-8 -*-
import os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np, cv2
ADB = r"E:\leidian\LDPlayer9\adb.exe"
OUT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\live"

def shot(tag):
    subprocess.run([ADB, "-s", "emulator-5554", "shell", "screencap", "-p", "/sdcard/_n_%s.png" % tag], capture_output=True, timeout=25)
    local = os.path.join(OUT, "_n_%s.png" % tag)
    subprocess.run([ADB, "-s", "emulator-5554", "pull", "/sdcard/_n_%s.png" % tag, local], capture_output=True, timeout=25)
    return cv2.imdecode(np.fromfile(local, np.uint8), cv2.IMREAD_COLOR)

def tap(x, y, wait=2.0):
    subprocess.run([ADB, "-s", "emulator-5554", "shell", "input", "tap", str(int(x)), str(int(y))], capture_output=True, timeout=20)
    time.sleep(wait)

img = shot("before")
print("before", img.shape)
tap(80, 650, 2.5)   # 战斗
img = shot("menu")
cv2.imencode(".png", img)[1].tofile(os.path.join(OUT, "nav_menu.png"))
print("menu saved", img.shape)

# 全屏 OCR 列出按钮文字
from rapidocr_onnxruntime import RapidOCR
engine = RapidOCR()
res, _ = engine(img)
items = sorted(res or [], key=lambda r: -((r[0][2][1]-r[0][0][1]) * (r[0][1][0]-r[0][0][0])))
seen = set()
for box, text, score in items[:40]:
    xs = [p[0] for p in box]; ys = [p[1] for p in box]
    cx, cy = sum(xs)/4, sum(ys)/4
    t = str(text).strip()
    if t in seen: continue
    seen.add(t)
    print("%-18s score=%.2f at (%.0f,%.0f)" % (t[:18], float(score), cx, cy))
