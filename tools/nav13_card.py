# -*- coding: utf-8 -*-
import os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
ADB = r"E:\leidian\LDPlayer9\adb.exe"; DEV = "emulator-5554"
OUT = os.path.join(BASE, "out", "live", "hires")
def sh(*a, timeout=90):
    return subprocess.run(list(a), capture_output=True, text=True, timeout=timeout)
def shot(tag):
    p = "/sdcard/s.png"
    sh(ADB, "-s", DEV, "shell", "screencap", "-p", p)
    dst = os.path.join(OUT, "nav_%s_%s.png" % (tag, time.strftime("%H%M%S")))
    sh(ADB, "-s", DEV, "pull", p, dst)
    from PIL import Image
    print("shot", dst, Image.open(dst).size if os.path.exists(dst) else "?")
    return dst
sh(ADB, "-s", DEV, "shell", "input", "tap", "1835", "70")   # 关闭商店
time.sleep(2)
sh(ADB, "-s", DEV, "shell", "input", "tap", "75", "530")    # 部落
time.sleep(3)
sh(ADB, "-s", DEV, "shell", "input", "tap", "1150", "430")  # 卡片本体
time.sleep(4)
shot("card_tap")
