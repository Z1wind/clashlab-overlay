# -*- coding: utf-8 -*-
import ctypes, os, subprocess, sys, time
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
subprocess.Popen([os.path.join(ROOT, "dist", "ClashOverlay.exe"), "--show", "--mode", "PANEL",
                  "--lang", "zh", "--allow-primary"], cwd=ROOT,
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
win = None
for i in range(12):
    time.sleep(1)
    ws = []
    def cb(h, _):
        if win32gui.IsWindowVisible(h) and win32gui.GetClassName(h) == "GLFW30":
            l, t, r, b = win32gui.GetWindowRect(h)
            ws.append((h, l, t, r, b))
        return True
    win32gui.EnumWindows(cb, None)
    good = [x for x in ws if abs((x[3]-x[1]) - 440) <= 12]
    if good:
        win = good[0]; print("t=%ds windows=%d chosen=%s" % (i+1, len(ws), win)); break
if win:
    h, x0, y0, x1, y1 = win
    u = ctypes.windll.user32
    def click(px):
        u.SetCursorPos(int(x0 + px), int(y0 + 25)); time.sleep(0.2)
        u.mouse_event(2, 0, 0, 0, 0); time.sleep(0.08); u.mouse_event(4, 0, 0, 0, 0)
        time.sleep(1.0)
        ImageGrab.grab(bbox=(x0, y0, x1, y1), all_screens=True).save(
            os.path.join(ROOT, "out", "live", "clean_%d.png" % px))
    for px in (292, 132, 212, 52, 132):
        click(px)
lines = open(LOG, "r", encoding="utf-8", errors="replace").readlines()[before:]
tail = [l.strip()[:110] for l in lines if ("another ClashLab" in l or "mouse-dbg" in l or "rect=" in l)]
print("log sample:", tail[-6:])
print("log lines:", len(lines))
