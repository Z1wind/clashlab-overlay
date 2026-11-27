# -*- coding: utf-8 -*-
"""QA2：双击默认启动、繁中、单实例（等待更久）。"""
import os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import ImageGrab
import win32gui
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
EXE = os.path.join(ROOT, "dist", "ClashOverlay.exe")
LOG = os.path.join(ROOT, "out", "overlay", "overlay.log")
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
# 1) 双击式启动（无参数）
subprocess.Popen([EXE], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(9)
print("no-arg windows:", wins())
kill(); time.sleep(1)
# 2) 繁中
before = sum(1 for _ in open(LOG, "r", encoding="utf-8", errors="replace"))
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
    ImageGrab.grab(bbox=(x0, y0, x1, y1), all_screens=True).save(os.path.join(ROOT, "out", "live", "qa_hant2.png"))
    print("saved qa_hant2")
# 3) 单实例（等 7 秒）
subprocess.Popen([EXE, "--show", "--mode", "PANEL", "--allow-primary"], cwd=ROOT,
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(7)
lines = open(LOG, "r", encoding="utf-8", errors="replace").readlines()[before:]
print("singleton log:", any("another ClashLab" in l for l in lines))
print("windows now:", len(wins()))
