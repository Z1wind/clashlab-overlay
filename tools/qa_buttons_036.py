# -*- coding: utf-8 -*-
"""QA：v0.3.6 面板设置页三按钮可见性。"""
import ctypes, os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import cv2, numpy as np
from PIL import ImageGrab
from rapidocr_onnxruntime import RapidOCR
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
if not win:
    raise SystemExit("no panel")
h, x0, y0, x1, y1 = win
u = ctypes.windll.user32
def click(px, py=25):
    u.SetCursorPos(int(x0 + px), int(y0 + py)); time.sleep(0.15)
    u.mouse_event(2, 0, 0, 0, 0); time.sleep(0.05); u.mouse_event(4, 0, 0, 0, 0)
    time.sleep(0.7)
click(220, 620); click(292)
img = ImageGrab.grab(bbox=(x0, y0, x1, y1), all_screens=True)
img.save(os.path.join(ROOT, "out", "live", "qa_buttons_036.png"))
arr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
E = RapidOCR(); res, _ = E(arr)
texts = [str(t) for _b, t, _s in (res or [])]
for want in ("生成战报", "启动标注器", "打开兵种"):
    print(want, "->", any(want in t for t in texts))
print("texts sample:", [t for t in texts if any(k in t for k in ("战报", "标注", "兵种"))][:6])
