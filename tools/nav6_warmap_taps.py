# -*- coding: utf-8 -*-
"""尝试多次点击部落战「去看看」并检测是否进入战争地图。"""
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
    return dst
attempts = [("touchscreen", "1100", "655"), ("tap", "1100", "660"), ("tap", "1120", "665"),
            ("touchscreen", "1100", "670"), ("tap", "1100", "645")]
for kind, x, y in attempts:
    cmd = ["shell", "input", kind, "tap", x, y] if kind == "touchscreen" else ["shell", "input", "tap", x, y]
    sh(ADB, "-s", DEV, *cmd)
    time.sleep(2.0)
dst = shot("after_taps")
print("shot:", dst)
