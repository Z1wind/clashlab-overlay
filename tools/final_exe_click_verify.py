# -*- coding: utf-8 -*-
import ctypes, os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import ImageGrab
import win32gui
import cv2, numpy as np
from rapidocr_onnxruntime import RapidOCR
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
EXE = os.path.join(ROOT, "dist", "ClashOverlay.exe")
subprocess.run(["powershell", "-NoProfile", "-Command",
                "Get-Process ClashOverlay -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue; "
                "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -like '*run_overlay.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"],
               capture_output=True, timeout=25)
time.sleep(1)
subprocess.Popen([EXE, "--show", "--mode", "PANEL", "--lang", "zh", "--allow-primary"],
                 cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
win = None
for i in range(15):
    time.sleep(1)
    found = []
    def cb(h, _):
        if win32gui.IsWindowVisible(h) and win32gui.GetClassName(h) == "GLFW30":
            l, t, r, b = win32gui.GetWindowRect(h)
            if abs((r - l) - 440) <= 12:
                found.append((h, l, t, r, b))
        return True
    win32gui.EnumWindows(cb, None)
    if found:
        win = found[0]; break
print("panel:", win)
E = RapidOCR()
if win:
    h, x0, y0, x1, y1 = win
    u = ctypes.windll.user32
    def click(px, py, times=1):
        for _ in range(times):
            u.SetCursorPos(int(x0 + px), int(y0 + py)); time.sleep(0.2)
            u.mouse_event(2, 0, 0, 0, 0); time.sleep(0.06); u.mouse_event(4, 0, 0, 0, 0)
            time.sleep(0.8)
    click(220, 620)  # 激活
    for name, px in (("research", 52), ("layout", 132), ("capture", 212), ("settings", 292)):
        click(px, 25, times=2)
        img = ImageGrab.grab(bbox=(x0, y0, x1, y1), all_screens=True)
        img.save(os.path.join(ROOT, "out", "live", "exefinal_%s.png" % name))
        arr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        res, _ = E(arr[-40:, :, :])
        print(name, "->", [str(t) for _, t, _ in (res or [])])
