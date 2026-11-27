# -*- coding: utf-8 -*-
"""把雷电实例 0 设为 1920x1080 横屏并启动，等游戏加载后截图。"""
import os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
LDCON = r"E:\leidian\LDPlayer9\ldconsole.exe"
ADB = r"E:\leidian\LDPlayer9\adb.exe"
DEV = "emulator-5554"
OUT = os.path.join(BASE, "out", "live", "hires")
os.makedirs(OUT, exist_ok=True)
def sh(*a, timeout=90):
    return subprocess.run(list(a), capture_output=True, text=True, timeout=timeout)
print("quit instance...", flush=True)
sh(LDCON, "quit", "--index", "0")
time.sleep(4)
print("modify resolution...", flush=True)
r = sh(LDCON, "modify", "--index", "0", "--resolution", "1920,1080,320")
print("modify:", (r.stdout or r.stderr).strip()[:120], flush=True)
print("launch...", flush=True)
sh(LDCON, "launch", "--index", "0")
for i in range(45):
    time.sleep(2)
    if DEV in (sh(ADB, "devices").stdout or ""):
        break
time.sleep(6)
print("wm size:", sh(ADB, "-s", DEV, "shell", "wm", "size").stdout.strip(), flush=True)
for k in range(5):
    time.sleep(8)
    adb = sh(ADB, "-s", DEV, "shell", "screencap", "-p", "/sdcard/shot.png")
    dst = os.path.join(OUT, "game_%s_%d.png" % (time.strftime("%H%M%S"), k + 1))
    sh(ADB, "-s", DEV, "pull", "/sdcard/shot.png", dst)
    from PIL import Image
    print("shot", dst, Image.open(dst).size if os.path.exists(dst) else "missing", flush=True)
print("done", flush=True)
