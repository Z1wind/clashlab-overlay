# -*- coding: utf-8 -*-
import ctypes, os, re, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import ImageGrab
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
LOG = os.path.join(ROOT, "out", "overlay", "overlay.log")
subprocess.run(["powershell", "-NoProfile", "-Command",
                "Get-Process ClashOverlay -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue"],
               capture_output=True, timeout=30)
time.sleep(2)
before = sum(1 for _ in open(LOG, "r", encoding="utf-8", errors="replace"))
subprocess.Popen([os.path.join(ROOT, "dist", "ClashOverlay.exe"), "--show", "--mode", "PANEL",
                  "--always-on-top", "--allow-primary"], cwd=ROOT,
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(7)
lines = open(LOG, "r", encoding="utf-8", errors="replace").readlines()[before:]
txt = "".join(lines)
print("draw errors:", txt.count("draw_panel error") + txt.count("draw frame error"))
ms = re.findall(r"win=\((\d+),(\d+),(\d+),(\d+)\)", txt)
print("win:", ms[-1] if ms else None)
if not ms:
    print(txt[-500:]); raise SystemExit
x0, y0, x1, y1 = [int(v) for v in ms[-1]]
w, h = x1 - x0, y1 - y0
u = ctypes.windll.user32
def click_and_grab(px, name):
    u.SetCursorPos(int(x0 + px), int(y0 + 25))
    time.sleep(0.15)
    u.mouse_event(2, 0, 0, 0, 0); time.sleep(0.05); u.mouse_event(4, 0, 0, 0, 0)
    time.sleep(0.9)
    p = os.path.join(ROOT, "out", "live", name)
    ImageGrab.grab(bbox=(x0, y0, x1, y1), all_screens=True).save(p)
    print("saved", p)
ImageGrab.grab(bbox=(x0, y0, x1, y1), all_screens=True).save(os.path.join(ROOT, "out", "live", "tab_research.png"))
print("saved research")
click_and_grab(135, "tab_capture.png")
click_and_grab(215, "tab_layout.png")
click_and_grab(295, "tab_settings.png")
print("rect:", (x0, y0, w, h))
