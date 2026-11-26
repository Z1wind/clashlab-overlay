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
time.sleep(8)
cands = []
def cb(h, _):
    t = win32gui.GetWindowText(h) or ""
    if win32gui.IsWindowVisible(h) and "ClashLab" in t:
        l, t0, r, b = win32gui.GetWindowRect(h)
        cands.append((h, l, t0, r, b))
    return True
win32gui.EnumWindows(cb, None)
print("candidates:", cands)
target = None
for c in cands:
    if abs((c[3] - c[1]) - 440) <= 8:
        target = c; break
print("chosen:", target)
if target:
    h, x0, y0, x1, y1 = target
    u = ctypes.windll.user32
    def click(px, py):
        u.SetCursorPos(int(x0 + px), int(y0 + py)); time.sleep(0.15)
        u.mouse_event(2, 0, 0, 0, 0); time.sleep(0.05); u.mouse_event(4, 0, 0, 0, 0)
        time.sleep(0.9)
    def grab(name):
        ImageGrab.grab(bbox=(x0, y0, x1, y1), all_screens=True).save(os.path.join(ROOT, "out", "live", name))
        print("saved", name)
    grab("en2_research.png")
    click(131, 25); grab("en2_capture.png")
    click(211, 25); grab("en2_layout.png")
    click(291, 25); grab("en2_settings.png")
