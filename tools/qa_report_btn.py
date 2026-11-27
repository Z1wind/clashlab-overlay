# -*- coding: utf-8 -*-
"""QA：点击「生成战报」按钮（无阵型时应有明确日志，不崩）。"""
import ctypes, os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
from PIL import ImageGrab
from rapidocr_onnxruntime import RapidOCR
import win32gui
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
EXE = os.path.join(ROOT, "dist", "ClashOverlay.exe")
LOG = os.path.join(ROOT, "out", "overlay", "overlay.log")
subprocess.run(["powershell", "-NoProfile", "-Command",
                "Get-Process ClashOverlay -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue"],
               capture_output=True, timeout=25)
time.sleep(1)
before = sum(1 for _ in open(LOG, "r", encoding="utf-8", errors="replace"))
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
h, x0, y0, x1, y1 = win
u = ctypes.windll.user32
def click(px, py=25):
    u.SetCursorPos(int(x0 + px), int(y0 + py)); time.sleep(0.15)
    u.mouse_event(2, 0, 0, 0, 0); time.sleep(0.05); u.mouse_event(4, 0, 0, 0, 0)
    time.sleep(0.8)
click(220, 640); click(292)
img = ImageGrab.grab(bbox=(x0, y0, x1, y1), all_screens=True)
arr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
E = RapidOCR(); res, _ = E(arr)
hit = None
for box, txt, _s in (res or []):
    if "生成战报" in str(txt):
        xs = [p[0] for p in box]; ys = [p[1] for p in box]
        hit = (sum(xs)/4, sum(ys)/4); break
print("button:", hit)
if hit:
    click(hit[0], hit[1])
    time.sleep(2.5)
lines = open(LOG, "r", encoding="utf-8", errors="replace").readlines()[before:]
for ln in lines:
    if "battle report" in ln.lower() or "战报" in ln:
        print("LOG:", ln.strip()[:160])
