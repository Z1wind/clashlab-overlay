# -*- coding: utf-8 -*-
import ctypes, os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import ImageGrab
import win32gui
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
EXE = os.path.join(ROOT, "dist", "ClashOverlay.exe")
subprocess.run(["powershell", "-NoProfile", "-Command",
                "Get-Process ClashOverlay -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue"],
               capture_output=True, timeout=20)
subprocess.Popen([EXE, "--show", "--mode", "PANEL", "--lang", "en", "--always-on-top", "--allow-primary"],
                 cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
found = None
for i in range(12):
    time.sleep(1)
    res = []
    def cb(h, _):
        if win32gui.IsWindowVisible(h) and "ClashLab" in (win32gui.GetWindowText(h) or ""):
            l, t, r, b = win32gui.GetWindowRect(h)
            res.append((h, l, t, r, b, r - l, b - t))
        return True
    win32gui.EnumWindows(cb, None)
    if res:
        print("t=%ds windows:" % (i + 1), res)
        found = res
        break
if found:
    h, x0, y0, x1, y1, w, hh = found[0]
    ImageGrab.grab(bbox=(x0, y0, x1, y1), all_screens=True).save(os.path.join(ROOT, "out", "live", "en4_research.png"))
    u = ctypes.windll.user32
    u.SetCursorPos(int(x0 + 291), int(y0 + 25)); time.sleep(0.15)
    u.mouse_event(2, 0, 0, 0, 0); time.sleep(0.05); u.mouse_event(4, 0, 0, 0, 0)
    time.sleep(1)
    ImageGrab.grab(bbox=(x0, y0, x1, y1), all_screens=True).save(os.path.join(ROOT, "out", "live", "en4_settings.png"))
    print("saved en4 screenshots", (x0, y0, x1, y1))
else:
    print("no window became visible in 12s")
