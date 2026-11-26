# -*- coding: utf-8 -*-
"""P0-2 + P1-4 自测：exe 面板点击切换（OCR 底栏）+ HUD 穿云箭截图。"""
import ctypes, hashlib, os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import ImageGrab
import win32gui
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
EXE = os.path.join(ROOT, "dist", "ClashOverlay.exe")
PY = r"D:\Python313\python.exe"
KILL = ("powershell", "-NoProfile", "-Command",
        "Get-Process ClashOverlay -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue")
def kill():
    subprocess.run(list(KILL), capture_output=True, timeout=20)
def wait_glfw(pred, tries=15):
    for _ in range(tries):
        time.sleep(1)
        found = []
        def cb(h, _):
            if win32gui.IsWindowVisible(h) and win32gui.GetClassName(h) == "GLFW30":
                l, t, r, b = win32gui.GetWindowRect(h)
                if pred(r - l, b - t):
                    found.append((h, l, t, r, b))
            return True
        win32gui.EnumWindows(cb, None)
        if found:
            return found[0]
    return None
u = ctypes.windll.user32
# --- exe PANEL 点击测试 ---
kill(); time.sleep(1)
subprocess.Popen([EXE, "--show", "--mode", "PANEL", "--lang", "zh", "--allow-primary"],
                 cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
win = wait_glfw(lambda w, h: abs(w - 440) <= 12)
print("panel win:", win)
if win:
    h, x0, y0, x1, y1 = win
    for i, (name, px) in enumerate((("research", 52), ("layout", 132), ("capture", 212), ("settings", 292))):
        # 第一次点击可能只激活窗口，点两次
        for _ in range(2):
            u.SetCursorPos(int(x0 + px), int(y0 + 25)); time.sleep(0.12)
            u.mouse_event(2, 0, 0, 0, 0); time.sleep(0.05); u.mouse_event(4, 0, 0, 0, 0)
            time.sleep(0.5)
        ImageGrab.grab(bbox=(x0, y0, x1, y1), all_screens=True).save(
            os.path.join(ROOT, "out", "live", "exe_tab_%s.png" % name))
    print("exe tab captures saved")
# --- HUD 穿云箭截图 ---
kill(); time.sleep(1)
subprocess.Popen([EXE, "--show", "--mode", "HUD", "--lang", "zh", "--always-on-top", "--allow-primary"],
                 cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
w = wait_glfw(lambda w, h: w > 600, tries=15)
print("hud win:", w)
if w:
    h, x0, y0, x1, y1 = w
    time.sleep(1)
    p = os.path.join(ROOT, "out", "live", "hud_arrow_verify.png")
    ImageGrab.grab(bbox=(x0, y0, x1, y1), all_screens=True).save(p)
    print("saved", p, (x0, y0, x1, y1), "size", (x1 - x0, y1 - y0))
