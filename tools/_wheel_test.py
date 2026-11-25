# -*- coding: utf-8 -*-
# 只读测试：前台 RenderWindow，连续鼠标滚轮，抓帧对比。
import ctypes, time, os, cv2, numpy as np
import win32gui
from ctypes import wintypes

user32 = ctypes.windll.user32
def find_render():
    out = []
    def cb(h, _):
        if win32gui.GetClassName(h) == "RenderWindow" and win32gui.IsWindowVisible(h):
            out.append(h)
    win32gui.EnumWindows(cb, None)
    # 递归找
    allc = []
    def collect(k):
        sub = []
        win32gui.EnumChildWindows(k, lambda x, _: sub.append(x), None)
        for x in sub:
            allc.append(x); collect(x)
    main = []
    win32gui.EnumWindows(lambda h, _: main.append(h) if win32gui.GetClassName(h) == "LDPlayerMainFrame" and win32gui.IsWindowVisible(h) else None, None)
    if main:
        collect(main[0])
        for x in allc:
            if win32gui.GetClassName(x) == "RenderWindow":
                return x
    return out[0] if out else None

h = find_render()
print("render hwnd", h)
if h:
    win32gui.ShowWindow(h, 9)  # SW_RESTORE
    user32.SwitchToThisWindow(h, True)
    time.sleep(0.5)
    # 鼠标移到 RenderWindow 中心
    r = win32gui.GetWindowRect(h)
    cx, cy = (r[0]+r[2])//2, (r[1]+r[3])//2
    ctypes.windll.user32.SetCursorPos(cx, cy)
    for i in range(8):
        ctypes.windll.user32.mouse_event(0x0800, 0, 0, -120, 0)  # WHEEL out
        time.sleep(0.4)
    time.sleep(1)

import subprocess
ADB = r"E:\leidian\LDPlayer9\adb.exe"
raw = subprocess.run([ADB, "exec-out", "screencap", "-p"], capture_output=True, timeout=30).stdout
im = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
cv2.imencode(".png", im)[1].tofile(r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\overlay\full\raw\wheel_test.png")
print("saved")
