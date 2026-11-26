# -*- coding: utf-8 -*-
import ctypes, os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import ImageGrab
import win32gui
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
EXE = os.path.join(ROOT, "dist", "ClashOverlay.exe")
def kill():
    subprocess.run(["powershell", "-NoProfile", "-Command",
                    "Get-Process ClashOverlay -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue"],
                   capture_output=True, timeout=20)
def find440():
    res = []
    def cb(h, _):
        if win32gui.IsWindowVisible(h) and "ClashLab" in (win32gui.GetWindowText(h) or ""):
            l, t, r, b = win32gui.GetWindowRect(h)
            if abs((r - l) - 440) <= 8:
                res.append((h, l, t, r, b))
        return True
    win32gui.EnumWindows(cb, None)
    return res
kill()
subprocess.Popen([EXE, "--show", "--mode", "PANEL", "--lang", "en", "--always-on-top", "--allow-primary"],
                 cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(4)
c = find440()
print("en window:", c)
if c:
    h, x0, y0, x1, y1 = c[0]
    p = os.path.join(ROOT, "out", "live", "en3_research.png")
    ImageGrab.grab(bbox=(x0, y0, x1, y1), all_screens=True).save(p)
    u = ctypes.windll.user32
    u.SetCursorPos(int(x0 + 291), int(y0 + 25)); time.sleep(0.15)
    u.mouse_event(2, 0, 0, 0, 0); time.sleep(0.05); u.mouse_event(4, 0, 0, 0, 0)
    time.sleep(0.8)
    p2 = os.path.join(ROOT, "out", "live", "en3_settings.png")
    ImageGrab.grab(bbox=(x0, y0, x1, y1), all_screens=True).save(p2)
    print("saved en3 screenshots")
kill()
subprocess.Popen([EXE, "--show", "--mode", "PANEL", "--always-on-top", "--allow-primary"],
                 cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2)
print("zh instance relaunched")
