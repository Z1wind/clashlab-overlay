# -*- coding: utf-8 -*-
import os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
ADB = r"E:\leidian\LDPlayer9\adb.exe"; DEV = "emulator-5554"
OUT = os.path.join(BASE, "out", "live", "hires")
def sh(*a, timeout=90):
    return subprocess.run(list(a), capture_output=True, text=True, timeout=timeout)
def tap(x, y, wait=3.0):
    sh(ADB, "-s", DEV, "shell", "input", "tap", str(x), str(y)); time.sleep(wait)
def shot(tag):
    p = "/sdcard/s.png"
    sh(ADB, "-s", DEV, "shell", "screencap", "-p", p)
    dst = os.path.join(OUT, "nav_%s_%s.png" % (tag, time.strftime("%H%M%S")))
    sh(ADB, "-s", DEV, "pull", p, dst)
    from PIL import Image
    print("shot", dst, Image.open(dst).size if os.path.exists(dst) else "?")
tap(75, 530, 3)      # 部落
shot("clan2")
tap(1100, 655, 4)    # 去看看
shot("warmap2")
