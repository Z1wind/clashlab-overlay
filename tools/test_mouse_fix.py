# -*- coding: utf-8 -*-
import ctypes, hashlib, os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import ImageGrab
import win32gui
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
PY = r"D:\Python313\python.exe"
subprocess.run(["powershell", "-NoProfile", "-Command",
                "Get-Process ClashOverlay -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue; "
                "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -like '*run_overlay.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"],
               capture_output=True, timeout=25)
time.sleep(1)
subprocess.Popen([PY, "-u", "run_overlay.py", "--show", "--mode", "PANEL", "--lang", "zh", "--allow-primary"],
                 cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
win = None
for i in range(15):
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
    hashes = {}
    for name, px in (("research", 52), ("layout", 132), ("capture", 212), ("settings", 292)):
        u.SetCursorPos(int(x0 + px), int(y0 + 25)); time.sleep(0.15)
        u.mouse_event(2, 0, 0, 0, 0); time.sleep(0.05); u.mouse_event(4, 0, 0, 0, 0)
        time.sleep(0.9)
        img = ImageGrab.grab(bbox=(x0, y0, x1, y1), all_screens=True)
        img.save(os.path.join(ROOT, "out", "live", "mf_%s.png" % name))
        hashes[name] = hashlib.md5(img.tobytes()).hexdigest()[:10]
    print("hashes:", hashes)
    print("distinct pages:", len(set(hashes.values())))
