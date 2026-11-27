# -*- coding: utf-8 -*-
import os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
from rapidocr_onnxruntime import RapidOCR
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
ADB = r"E:\leidian\LDPlayer9\adb.exe"; DEV = "emulator-5554"
def sh(*a):
    return subprocess.run(list(a), capture_output=True, text=True, timeout=90)
sh(ADB, "-s", DEV, "shell", "screencap", "-p", "/sdcard/s.png")
dst = os.path.join(BASE, "out", "live", "hires", "prep_check.png")
sh(ADB, "-s", DEV, "pull", "/sdcard/s.png", dst)
img = cv2.imdecode(np.fromfile(dst, np.uint8), cv2.IMREAD_COLOR)
E = RapidOCR(); res, _ = E(img)
texts = [str(t) for _b, t, _s in (res or [])]
print("game state:", " | ".join(texts[:14]))
print("has reload:", any("重新载入" in t for t in texts), "| has 准备日:", any("准备日" in t for t in texts), "| has 敌军:", any("敌军" in t for t in texts))
