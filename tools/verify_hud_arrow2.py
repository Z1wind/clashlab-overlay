# -*- coding: utf-8 -*-
import os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import ImageGrab
import win32gui
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
LOG = os.path.join(ROOT, "out", "overlay", "overlay.log")
subprocess.run(["powershell", "-NoProfile", "-Command",
                "Get-Process ClashOverlay -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue; "
                "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -like '*run_overlay.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"],
               capture_output=True, timeout=25)
time.sleep(1)
before = sum(1 for _ in open(LOG, "r", encoding="utf-8", errors="replace"))
subprocess.Popen([r"D:\Python313\python.exe", "-u", "run_overlay.py", "--show", "--mode", "HUD",
                  "--lang", "zh", "--always-on-top", "--allow-primary"],
                 cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
win = None
for i in range(15):
    time.sleep(1)
    found = []
    def cb(h, _):
        if win32gui.IsWindowVisible(h) and win32gui.GetClassName(h) == "GLFW30":
            l, t, r, b = win32gui.GetWindowRect(h)
            if r - l > 600:
                found.append((h, l, t, r, b))
        return True
    win32gui.EnumWindows(cb, None)
    if found:
        win = found[0]; break
print("hud win:", win)
time.sleep(1)
lines = open(LOG, "r", encoding="utf-8", errors="replace").readlines()[before:]
for ln in lines:
    if "hud-arrow" in ln:
        print("LOG:", ln.strip())
if win:
    h, x0, y0, x1, y1 = win
    p = os.path.join(ROOT, "out", "live", "hud_arrow_verify2.png")
    ImageGrab.grab(bbox=(x0, y0, x1, y1), all_screens=True).save(p)
    print("saved", p)
