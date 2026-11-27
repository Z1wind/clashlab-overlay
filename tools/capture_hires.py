# -*- coding: utf-8 -*-
"""高分辨率截图：启动/复用雷电实例，尝试 wm size 提升分辨率，截图后恢复。"""
import argparse, glob, os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
ADB = r"E:\leidian\LDPlayer9\adb.exe"
LDCON = r"E:\leidian\LDPlayer9\ldconsole.exe"
DEV = "emulator-5554"
OUT = os.path.join(BASE, "out", "live", "hires")
os.makedirs(OUT, exist_ok=True)

def sh(*args, timeout=60):
    return subprocess.run(list(args), capture_output=True, text=True, timeout=timeout)

def adb(*args, timeout=60):
    return sh(ADB, "-s", DEV, *args, timeout=timeout)

def wait_device(seconds=90):
    t0 = time.time()
    while time.time() - t0 < seconds:
        r = sh(ADB, "devices")
        if DEV in (r.stdout or ""):
            time.sleep(3)
            return True
        time.sleep(2)
    return False

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", default="1920x1080")
    ap.add_argument("--keep-size", action="store_true")
    ap.add_argument("--no-start", action="store_true")
    a = ap.parse_args()
    r = sh(ADB, "devices")
    if DEV not in (r.stdout or ""):
        if a.no_start:
            print("device not running and --no-start set"); return 2
        print("starting LDPlayer instance 0 ...", flush=True)
        sh(LDCON, "launch", "--index", "0")
        if not wait_device():
            print("device did not come up"); return 3
    cur = adb("shell", "wm", "size")
    print("current:", cur.stdout.strip() or cur.stderr.strip())
    orig = None
    if a.size and a.size != "off":
        adb("shell", "wm", "size", a.size)
        time.sleep(2)
        print("boosting to", a.size, flush=True)
    adb("shell", "screencap", "-p", "/sdcard/hires_shot.png")
    dst = os.path.join(OUT, "shot_%s.png" % time.strftime("%Y%m%d_%H%M%S"))
    sh(ADB, "-s", DEV, "pull", "/sdcard/hires_shot.png", dst)
    from PIL import Image
    if os.path.exists(dst):
        print("saved:", dst, Image.open(dst).size)
    if a.size and a.size != "off" and not a.keep_size:
        adb("shell", "wm", "size", "reset")
        print("size reset")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
