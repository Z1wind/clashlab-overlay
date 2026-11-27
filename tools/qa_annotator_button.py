# -*- coding: utf-8 -*-
"""QA：面板设置页点「启动标注器」→ 验证 8765 HTTP 200 + 日志。"""
import ctypes, os, subprocess, sys, time, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import ImageGrab
import win32gui
import cv2, numpy as np
from rapidocr_onnxruntime import RapidOCR
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
EXE = os.path.join(ROOT, "dist", "ClashOverlay.exe")
LOG = os.path.join(ROOT, "out", "overlay", "overlay.log")
subprocess.run(["powershell", "-NoProfile", "-Command",
                "Get-Process ClashOverlay -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue; "
                "Get-NetTCPConnection -LocalPort 8765 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }"],
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
if not win:
    raise SystemExit("no panel")
h, x0, y0, x1, y1 = win
u = ctypes.windll.user32
def click(px, py):
    u.SetCursorPos(int(x0 + px), int(y0 + py)); time.sleep(0.15)
    u.mouse_event(2, 0, 0, 0, 0); time.sleep(0.05); u.mouse_event(4, 0, 0, 0, 0)
    time.sleep(0.8)
click(220, 640)   # 激活
click(292, 25)    # 设置页
img = ImageGrab.grab(bbox=(x0, y0, x1, y1), all_screens=True)
img.save(os.path.join(ROOT, "out", "live", "qa_annotator_btn.png"))
arr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
E = RapidOCR()
res, _ = E(arr)
target = None
for box, txt, score in (res or []):
    if "启动标注器" in str(txt):
        xs = [p[0] for p in box]; ys = [p[1] for p in box]
        target = (sum(xs) / 4, sum(ys) / 4)
        break
print("button pos:", target)
if target:
    click(target[0], target[1])
    time.sleep(3)
try:
    with urllib.request.urlopen("http://127.0.0.1:8765/", timeout=6) as r:
        print("annotator HTTP", r.status, "bytes", len(r.read()))
except Exception as e:
    print("annotator FAIL:", str(e)[:120])
lines = open(LOG, "r", encoding="utf-8", errors="replace").readlines()[before:]
for ln in lines:
    if "annotator" in ln.lower():
        print("LOG:", ln.strip()[:140])
