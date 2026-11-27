# -*- coding: utf-8 -*-
"""测试断线重连路径：OCR 找「重新载入游戏」并点击，等 25 秒后截图检查。"""
import os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
from rapidocr_onnxruntime import RapidOCR
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
ADB = r"E:\leidian\LDPlayer9\adb.exe"; DEV = "emulator-5554"
OUT = os.path.join(BASE, "out", "live", "hires")
def sh(*a):
    return subprocess.run(list(a), capture_output=True, text=True, timeout=90)
def cap(name):
    sh(ADB, "-s", DEV, "shell", "screencap", "-p", "/sdcard/s.png")
    dst = os.path.join(OUT, name)
    sh(ADB, "-s", DEV, "pull", "/sdcard/s.png", dst)
    return cv2.imdecode(np.fromfile(dst, np.uint8), cv2.IMREAD_COLOR)
def ocr_texts(img):
    E = RapidOCR(); res, _ = E(img)
    return [(b, str(t)) for b, t, _s in (res or [])]
img = cap("reconnect_before.png")
hit = None
for b, t in ocr_texts(img):
    if "重新载入" in t:
        xs = [p[0] for p in b]; ys = [p[1] for p in b]
        hit = (sum(xs)/4, sum(ys)/4); break
print("reload hit:", hit)
if hit:
    sh(ADB, "-s", DEV, "shell", "input", "tap", str(int(hit[0])), str(int(hit[1])))
    for i in range(4):
        time.sleep(9)
        im = cap("reconnect_after_%d.png" % (i + 1))
        texts = [t for _b, t in ocr_texts(im)]
        print(i, "texts:", " | ".join(texts[:10]))
