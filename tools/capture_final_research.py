# -*- coding: utf-8 -*-
import ctypes, os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import ImageGrab
import win32gui
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
EXE = os.path.join(ROOT, "dist", "ClashOverlay.exe")
subprocess.Popen([EXE, "--show", "--mode", "PANEL", "--lang", "en", "--always-on-top", "--allow-primary"],
                 cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
win = None
for i in range(12):
    time.sleep(1)
    def cb(h, _):
        global win
        if win is None and win32gui.IsWindowVisible(h) and win32gui.GetClassName(h) == "GLFW30":
            l, t, r, b = win32gui.GetWindowRect(h)
            if abs((r - l) - 440) <= 12:
                win = (h, l, t, r, b)
        return True
    win32gui.EnumWindows(cb, None)
    if win: break
print("win:", win)
if win:
    h, x0, y0, x1, y1 = win
    u = ctypes.windll.user32
    u.SetCursorPos(int(x0 + 52), int(y0 + 25)); time.sleep(0.15)
    u.mouse_event(2, 0, 0, 0, 0); time.sleep(0.05); u.mouse_event(4, 0, 0, 0, 0)
    time.sleep(1.0)
    ImageGrab.grab(bbox=(x0, y0, x1, y1), all_screens=True).save(os.path.join(ROOT, "out", "live", "final_en_research.png"))
    print("saved final_en_research.png")
