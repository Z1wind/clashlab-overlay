# -*- coding: utf-8 -*-
import os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat")
import numpy as np, cv2
from rapidocr_onnxruntime import RapidOCR
ADB = r"E:\leidian\LDPlayer9\adb.exe"
OUT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\live"
ENGINE = RapidOCR()

def shot(tag):
    subprocess.run([ADB, "-s", "emulator-5554", "shell", "screencap", "-p", "/sdcard/_t_%s.png" % tag], capture_output=True, timeout=25)
    local = os.path.join(OUT, "_t_%s.png" % tag)
    subprocess.run([ADB, "-s", "emulator-5554", "pull", "/sdcard/_t_%s.png" % tag, local], capture_output=True, timeout=25)
    return cv2.imdecode(np.fromfile(local, np.uint8), cv2.IMREAD_COLOR)

def tap(x, y, wait=1.5):
    subprocess.run([ADB, "-s", "emulator-5554", "shell", "input", "tap", str(int(x)), str(int(y))], capture_output=True, timeout=20)
    time.sleep(wait)

def texts(img):
    res, _ = ENGINE(img)
    return [str(t) for _, t, _ in (res or [])]

# 先验证 战斗 按钮打开菜单
tap(80, 650)
print("after 战斗:", texts(shot("a"))[:12], flush=True)
subprocess.run([ADB, "-s", "emulator-5554", "shell", "input", "keyevent", "4"], capture_output=True, timeout=20)
time.sleep(1.5)
# 尝试多个左侧图标坐标
for (x, y) in ((55, 285), (45, 285), (70, 285), (55, 300), (55, 345)):
    tap(x, y, 1.2)
    t = texts(shot("p%d_%d" % (x, y)))
    flag = any(k in " ".join(t) for k in ("部落战", "成员", "战争", "部落"))
    print("tap", (x, y), "->", t[:10], "clan?", flag, flush=True)
    if flag:
        break
    subprocess.run([ADB, "-s", "emulator-5554", "shell", "input", "keyevent", "4"], capture_output=True, timeout=20)
    time.sleep(1.2)
