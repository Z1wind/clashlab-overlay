# -*- coding: utf-8 -*-
import os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
from rapidocr_onnxruntime import RapidOCR
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
ADB = r"E:\leidian\LDPlayer9\adb.exe"; DEV = "emulator-5554"
OUT = os.path.join(BASE, "out", "live", "hires")
def sh(*a, timeout=90):
    return subprocess.run(list(a), capture_output=True, text=True, timeout=timeout)
def cap(tag):
    sh(ADB, "-s", DEV, "shell", "screencap", "-p", "/sdcard/s.png")
    dst = os.path.join(OUT, "scout_%s_%s.png" % (tag, time.strftime("%H%M%S")))
    sh(ADB, "-s", DEV, "pull", "/sdcard/s.png", dst)
    img = cv2.imdecode(np.fromfile(dst, np.uint8), cv2.IMREAD_COLOR)
    print("cap", dst, None if img is None else img.shape)
    return img, dst
def tap_ocr(img, keyword):
    E = RapidOCR(); res, _ = E(img)
    for box, txt, _s in (res or []):
        if keyword in str(txt):
            xs = [p[0] for p in box]; ys = [p[1] for p in box]
            x, y = int(sum(xs)/4), int(sum(ys)/4)
            sh(ADB, "-s", DEV, "shell", "input", "tap", str(x), str(y))
            print("tap", keyword, x, y)
            return True
    print("not found", keyword)
    return False
sh(ADB, "-s", DEV, "shell", "input", "tap", "1150", "470")  # 2号基地
time.sleep(3)
img, _ = cap("profile")
tap_ocr(img, "侦察")
time.sleep(5)
cap("enemybase")
