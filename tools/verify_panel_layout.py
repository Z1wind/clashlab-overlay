# -*- coding: utf-8 -*-
import ctypes, os, re, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import ImageGrab
PY = r"D:\Python313\python.exe"
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
LOG = os.path.join(ROOT, "out", "logs", "panel_layout.log")
f = open(LOG, "w", encoding="utf-8")
pid = subprocess.Popen([PY, "-u", "run_overlay.py", "--show", "--mode", "PANEL", "--lang", "zh",
                        "--run-seconds", "22", "--always-on-top", "--allow-primary"],
                       cwd=ROOT, stdout=f, stderr=subprocess.STDOUT)
time.sleep(6)
f.flush()
txt = open(LOG, encoding="utf-8", errors="replace").read()
m = re.search(r"rect=\((\d+),(\d+),(\d+)x(\d+)\)", txt)
print("draw errors:", txt.count("draw_panel error"))
print("rect:", m.group(0) if m else "none")
if m:
    x, y, w, h = [int(v) for v in m.groups()]
    img = ImageGrab.grab(bbox=(x, y, x + w, y + h), all_screens=True)
    p1 = os.path.join(ROOT, "out", "live", "panel_fixed_research.png")
    img.save(p1)
    print("saved", p1)
    # 点「设置」tab（第 4 个，标签条被语言按钮压缩后的中心）
    u = ctypes.windll.user32
    u.SetCursorPos(x + 292, y + 25)
    time.sleep(0.2)
    u.mouse_event(2, 0, 0, 0, 0); time.sleep(0.05); u.mouse_event(4, 0, 0, 0, 0)
    time.sleep(1.0)
    img2 = ImageGrab.grab(bbox=(x, y, x + w, y + h), all_screens=True)
    p2 = os.path.join(ROOT, "out", "live", "panel_fixed_settings.png")
    img2.save(p2)
    print("saved", p2)
pid.wait(timeout=40)
