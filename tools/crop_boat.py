# -*- coding: utf-8 -*-
import os, subprocess, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np, cv2
ADB = r"E:\leidian\LDPlayer9\adb.exe"
OUT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\live"
subprocess.run([ADB, "-s", "emulator-5554", "shell", "screencap", "-p", "/sdcard/_s.png"], capture_output=True, timeout=20)
subprocess.run([ADB, "-s", "emulator-5554", "pull", "/sdcard/_s.png", os.path.join(OUT, "_now.png")], capture_output=True, timeout=20)
img = cv2.imdecode(np.fromfile(os.path.join(OUT, "_now.png"), np.uint8), cv2.IMREAD_COLOR)
print("frame", img.shape)
crop = img[240:580, 1080:1280]
crop = cv2.resize(crop, None, fx=3, fy=3, interpolation=cv2.INTER_NEAREST)
cv2.imencode(".png", crop)[1].tofile(os.path.join(OUT, "boat_crop.png"))
print("saved boat_crop.png (crop x1080-1280 y240-580, 3x)")
