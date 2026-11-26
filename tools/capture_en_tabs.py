# -*- coding: utf-8 -*-
import ctypes, os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import ImageGrab
import win32gui
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
subprocess.run(["powershell", "-NoProfile", "-Command",
                "Get-Process ClashOverlay -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue"],
               capture_output=True, timeout=30)
time.sleep(2)
subprocess.Popen([os.path.join(ROOT, "dist", "ClashOverlay.exe"), "--show", "--mode", "PANEL",
                  "--lang", "en", "--always-on-top", "--allow-primary"], cwd=ROOT,
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(7)
hwnd = None
def cb(h, _):
    global hwnd
    if win32gui.IsWindowVisible(h) and "ClashLab" in (win32gui.GetWindowText(h) or ""):
        hwnd = h
    return True
win32gui.EnumWindows(cb, None)
print("overlay hwnd:", hwnd)
if hwnd:
    x0, y0, x1, y1 = win32gui.GetWindowRect(hwnd)
    print("rect:", (x0, y0, x1, y1))
    u = ctypes.windll.user32
    def click(px, py):
        u.SetCursorPos(int(x0 + px), int(y0 + py)); time.sleep(0.15)
        u.mouse_event(2, 0, 0, 0, 0); time.sleep(0.05); u.mouse_event(4, 0, 0, 0, 0)
        time.sleep(0.9)
    def grab(name):
        ImageGrab.grab(bbox=(x0, y0, x1, y1), all_screens=True).save(os.path.join(ROOT, "out", "live", name))
        print("saved", name)
    grab("en_tab_research.png")
    click(131, 25); grab("en_tab_capture.png")
    click(211, 25); grab("en_tab_layout.png")
    click(291, 25); grab("en_tab_settings.png")
