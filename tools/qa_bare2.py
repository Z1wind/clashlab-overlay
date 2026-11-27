# -*- coding: utf-8 -*-
import os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import ImageGrab
import win32gui
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
EXE = os.path.join(ROOT, "dist", "ClashOverlay.exe")
subprocess.run(["powershell", "-NoProfile", "-Command",
                "Get-Process ClashOverlay -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue"],
               capture_output=True, timeout=25)
time.sleep(1)
subprocess.Popen([EXE], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
w = None
for _ in range(16):
    time.sleep(1)
    out = []
    def cb(h, _):
        if win32gui.IsWindowVisible(h) and win32gui.GetClassName(h) == "GLFW30":
            l, t, r, b = win32gui.GetWindowRect(h)
            out.append((h, l, t, r, b))
        return True
    win32gui.EnumWindows(cb, None)
    g = [x for x in out if abs((x[3] - x[1]) - 440) <= 12]
    if g:
        w = g[0]; break
print("bare launch panel:", w)
if w:
    h, x0, y0, x1, y1 = w
    ImageGrab.grab(bbox=(x0, y0, x1, y1), all_screens=True).save(os.path.join(ROOT, "out", "live", "qa_bare2.png"))
    print("saved qa_bare2")
