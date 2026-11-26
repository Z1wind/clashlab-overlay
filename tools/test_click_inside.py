# -*- coding: utf-8 -*-
import ctypes, os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import win32gui
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
LOG = os.path.join(ROOT, "out", "overlay", "overlay.log")
subprocess.run(["powershell", "-NoProfile", "-Command",
                "Get-Process ClashOverlay -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue"],
               capture_output=True, timeout=20)
subprocess.Popen([os.path.join(ROOT, "dist", "ClashOverlay.exe"), "--show", "--mode", "PANEL",
                  "--always-on-top", "--allow-primary"], cwd=ROOT,
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
    if win:
        break
print("win:", win)
if win:
    h, x0, y0, x1, y1 = win
    before = sum(1 for _ in open(LOG, "r", encoding="utf-8", errors="replace"))
    u = ctypes.windll.user32
    u.SetCursorPos(int(x0 + 212), int(y0 + 25)); time.sleep(0.2)
    u.mouse_event(2, 0, 0, 0, 0); time.sleep(0.08); u.mouse_event(4, 0, 0, 0, 0)
    time.sleep(1.0)
    new = open(LOG, "r", encoding="utf-8", errors="replace").readlines()[before:]
    for ln in new[-8:]:
        print(ln.strip()[:130])
