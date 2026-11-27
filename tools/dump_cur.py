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
dst = os.path.join(BASE, "out", "live", "hires", "cur_state.png")
sh(ADB, "-s", DEV, "pull", "/sdcard/s.png", dst)
img = cv2.imdecode(np.fromfile(dst, np.uint8), cv2.IMREAD_COLOR)
print("shape", img.shape)
E = RapidOCR(); res, _ = E(img)
for item in (res or []):
    box, txt, score = item[0], item[1], item[2]
    xs = [p[0] for p in box]; ys = [p[1] for p in box]
    print("%-16s (%d,%d)" % (str(txt)[:16], sum(xs)/4, sum(ys)/4))
