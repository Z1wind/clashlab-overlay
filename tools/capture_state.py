# -*- coding: utf-8 -*-
import os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np, cv2
ADB = r"E:\leidian\LDPlayer9\adb.exe"
OUT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\live"
subprocess.run([ADB, "-s", "emulator-5554", "shell", "screencap", "-p", "/sdcard/_state.png"], capture_output=True, timeout=25)
subprocess.run([ADB, "-s", "emulator-5554", "pull", "/sdcard/_state.png", os.path.join(OUT, "state_now.png")], capture_output=True, timeout=25)
print("saved state_now.png")
