# -*- coding: utf-8 -*-
import ctypes, os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import ImageGrab
import win32gui
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
EXE = os.path.join(ROOT, "dist", "ClashOverlay.exe")
KILL = ("powershell", "-NoProfile", "-Command",
        "Get-Process ClashOverlay -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue; "
        "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -like '*run_overlay.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }")
subprocess.run(list(KILL), capture_output=True, timeout=30)
time.sleep(1)
u = ctypes.windll.user32

def windows():
    out = []
    def cb(h, _):
        if win32gui.IsWindowVisible(h) and win32gui.GetClassName(h) == "GLFW30":
            l, t, r, b = win32gui.GetWindowRect(h)
            out.append((h, l, t, r, b))
        return True
    win32gui.EnumWindows(cb, None)
    return out

def run(lang, tag):
    subprocess.Popen([EXE, "--show", "--mode", "PANEL", "--lang", lang, "--always-on-top", "--allow-primary"],
                     cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    win = None
    for i in range(15):
        time.sleep(1)
        ws = windows()
        good = [w for w in ws if abs((w[3] - w[1]) - 440) <= 12 and w[1] > -500]
        if good:
            win = good[0]; break
    print(tag, "windows:", windows(), "chosen:", win)
    if not win:
        return
    h, x0, y0, x1, y1 = win
    def click(px, py):
        u.SetCursorPos(int(x0 + px), int(y0 + py)); time.sleep(0.12)
        u.mouse_event(2, 0, 0, 0, 0); time.sleep(0.04); u.mouse_event(4, 0, 0, 0, 0)
        time.sleep(0.8)
    def grab(name):
        ImageGrab.grab(bbox=(x0, y0, x1, y1), all_screens=True).save(os.path.join(ROOT, "out", "live", name))
    grab(tag + "_research.png")
    click(211, 25); grab(tag + "_layout.png")
    click(291, 25); grab(tag + "_settings.png")
    click(131, 25); grab(tag + "_capture.png")
    print(tag, "captured 4 pages")

run("zh", "self_zh")
subprocess.run(list(KILL), capture_output=True, timeout=30)
time.sleep(1)
run("en", "self_en")
subprocess.run(list(KILL), capture_output=True, timeout=30)
subprocess.Popen([EXE, "--show", "--mode", "PANEL", "--always-on-top", "--allow-primary"],
                 cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("zh instance relaunched for user")
