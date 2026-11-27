# -*- coding: utf-8 -*-
"""QA3：新 exe 双击可见 / 繁中 / 版本号。"""
import os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import ImageGrab
import win32gui
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
EXE = os.path.join(ROOT, "dist", "ClashOverlay.exe")
def kill():
    subprocess.run(["powershell", "-NoProfile", "-Command",
                    "Get-Process ClashOverlay -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue"],
                   capture_output=True, timeout=25)
def wins():
    out = []
    def cb(h, _):
        if win32gui.IsWindowVisible(h) and win32gui.GetClassName(h) == "GLFW30":
            l, t, r, b = win32gui.GetWindowRect(h)
            out.append((h, l, t, r, b))
        return True
    win32gui.EnumWindows(cb, None)
    return out
kill(); time.sleep(1)
r = subprocess.run([EXE, "--version"], capture_output=True, text=True, timeout=30)
print("version:", (r.stdout or r.stderr).strip()[:60])
# 双击式启动
subprocess.Popen([EXE], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
w = None
for _ in range(15):
    time.sleep(1)
    g = [x for x in wins() if abs((x[3] - x[1]) - 440) <= 12]
    if g:
        w = g[0]; break
print("bare launch panel:", w)
if w:
    h, x0, y0, x1, y1 = w
    ImageGrab.grab(bbox=(x0, y0, x1, y1), all_screens=True).save(os.path.join(ROOT, "out", "live", "qa_bare.png"))
kill(); time.sleep(1)
# 繁中
subprocess.Popen([EXE, "--show", "--mode", "PANEL", "--lang", "zh-hant", "--allow-primary"],
                 cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
w = None
for _ in range(15):
    time.sleep(1)
    g = [x for x in wins() if abs((x[3] - x[1]) - 440) <= 12]
    if g:
        w = g[0]; break
print("hant panel:", w)
if w:
    h, x0, y0, x1, y1 = w
    ImageGrab.grab(bbox=(x0, y0, x1, y1), all_screens=True).save(os.path.join(ROOT, "out", "live", "qa_hant3.png"))
