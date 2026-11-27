# -*- coding: utf-8 -*-
import ctypes, os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import ImageGrab
import win32gui
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
EXE = os.path.join(ROOT, "dist", "ClashOverlay.exe")
subprocess.run(["powershell", "-NoProfile", "-Command",
                "Get-Process ClashOverlay -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue"],
               capture_output=True, timeout=25)
time.sleep(1)
subprocess.Popen([EXE, "--show", "--mode", "PANEL", "--lang", "zh", "--allow-primary"],
                 cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
win = None
for _ in range(15):
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
        win = g[0]; break
print("panel:", win)
if win:
    h, x0, y0, x1, y1 = win
    u = ctypes.windll.user32
    def click(px, py=25):
        u.SetCursorPos(int(x0 + px), int(y0 + py)); time.sleep(0.15)
        u.mouse_event(2, 0, 0, 0, 0); time.sleep(0.05); u.mouse_event(4, 0, 0, 0, 0)
        time.sleep(0.7)
    click(220, 620)
    click(292)  # 设置页
    ImageGrab.grab(bbox=(x0, y0, x1, y1), all_screens=True).save(os.path.join(ROOT, "out", "live", "qa_units_btn.png"))
    print("saved qa_units_btn.png")
