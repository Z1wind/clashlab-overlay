# -*- coding: utf-8 -*-
"""OCR 定位按钮并点击：通用工具。"""
import os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
from rapidocr_onnxruntime import RapidOCR
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
ADB = r"E:\leidian\LDPlayer9\adb.exe"; DEV = "emulator-5554"
OUT = os.path.join(BASE, "out", "live", "hires")
def sh(*a, timeout=90):
    return subprocess.run(list(a), capture_output=True, text=True, timeout=timeout)
def cap():
    p = "/sdcard/s.png"
    sh(ADB, "-s", DEV, "shell", "screencap", "-p", p)
    dst = os.path.join(OUT, "cur.png")
    sh(ADB, "-s", DEV, "pull", p, dst)
    return cv2.imdecode(np.fromfile(dst, np.uint8), cv2.IMREAD_COLOR)
def find(img, keyword):
    E = RapidOCR()
    res, _ = E(img)
    for box, txt, score in (res or []):
        if keyword in str(txt):
            xs = [p[0] for p in box]; ys = [p[1] for p in box]
            return int(sum(xs)/4), int(sum(ys)/4), str(txt)
    return None
img = cap()
hit = find(img, "敌军")
print("敌军 hit:", hit)
if hit:
    sh(ADB, "-s", DEV, "shell", "input", "tap", str(hit[0]), str(hit[1]))
    time.sleep(3.5)
    dst = os.path.join(OUT, "war_enemy2_%s.png" % time.strftime("%H%M%S"))
    sh(ADB, "-s", DEV, "shell", "screencap", "-p", "/sdcard/s.png")
    sh(ADB, "-s", DEV, "pull", "/sdcard/s.png", dst)
    print("shot", dst)
