# -*- coding: utf-8 -*-
import os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
ADB = r"E:\leidian\LDPlayer9\adb.exe"; DEV = "emulator-5554"
OUT = os.path.join(BASE, "out", "live", "hires")
os.makedirs(OUT, exist_ok=True)
def sh(*a, timeout=120):
    return subprocess.run(list(a), capture_output=True, text=True, timeout=timeout)
# 找 CoC 包名
r = sh(ADB, "-s", DEV, "shell", "pm", "list", "packages", "|", "grep", "-i", "clash")
print("pkgs:", (r.stdout or r.stderr).strip()[:300])
pkg = None
for line in (r.stdout or "").splitlines():
    if "clashofclans" in line.lower():
        pkg = line.replace("package:", "").strip()
print("pkg:", pkg)
if pkg:
    sh(ADB, "-s", DEV, "shell", "monkey", "-p", pkg, "-c", "android.intent.category.LAUNCHER", "1")
    for k in range(6):
        time.sleep(10)
        p = "/sdcard/game_%d.png" % k
        sh(ADB, "-s", DEV, "shell", "screencap", "-p", p)
        dst = os.path.join(OUT, "coc_%s_%d.png" % (time.strftime("%H%M%S"), k + 1))
        sh(ADB, "-s", DEV, "pull", p, dst)
        from PIL import Image
        print("shot", dst, Image.open(dst).size if os.path.exists(dst) else "?", flush=True)
