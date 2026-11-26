# -*- coding: utf-8 -*-
import os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import numpy as np, cv2
ADB = r"E:\leidian\LDPlayer9\adb.exe"
OUT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\live"
# 唯一一次导航点击：夜世界右上角小船（返回主世界）
subprocess.run([ADB, "-s", "emulator-5554", "shell", "input", "tap", "1215", "177"], capture_output=True, timeout=20)
print("tapped boat (1215,177)")
for i in range(4):
    time.sleep(4)
    subprocess.run([ADB, "-s", "emulator-5554", "shell", "screencap", "-p", "/sdcard/_shot_boat.png"], capture_output=True, timeout=25)
    subprocess.run([ADB, "-s", "emulator-5554", "pull", "/sdcard/_shot_boat.png", os.path.join(OUT, "after_boat.png")], capture_output=True, timeout=25)
    img = cv2.imdecode(np.fromfile(os.path.join(OUT, "after_boat.png"), np.uint8), cv2.IMREAD_COLOR)
    print("[%d] frame %s" % (i, None if img is None else img.shape))
print("done")
