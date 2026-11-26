# -*- coding: utf-8 -*-
import os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np, cv2
ADB = r"E:\leidian\LDPlayer9\adb.exe"
OUT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\live"
def shot(tag):
    remote = "/sdcard/_shot_%s.png" % tag
    subprocess.run([ADB, "-s", "emulator-5554", "shell", "screencap", "-p", remote], capture_output=True, timeout=25)
    local = os.path.join(OUT, "_shot_%s.png" % tag)
    r = subprocess.run([ADB, "-s", "emulator-5554", "pull", remote, local], capture_output=True, timeout=25)
    if not os.path.exists(local) or os.path.getsize(local) < 10000:
        print("pull failed", r.stderr[:120]); return None
    img = cv2.imdecode(np.fromfile(local, np.uint8), cv2.IMREAD_COLOR)
    print(tag, "frame", None if img is None else img.shape)
    return img
img = shot("now")
if img is not None:
    crop = img[240:580, 1080:1280]
    crop = cv2.resize(crop, None, fx=3, fy=3, interpolation=cv2.INTER_NEAREST)
    cv2.imencode(".png", crop)[1].tofile(os.path.join(OUT, "boat_crop.png"))
    print("saved boat_crop.png")
