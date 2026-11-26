# -*- coding: utf-8 -*-
import os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import Image, ImageGrab
PY = r"D:\Python313\python.exe"
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
f = open(os.path.join(ROOT, "out", "logs", "panel_en2.log"), "w", encoding="utf-8")
pid = subprocess.Popen([PY, "run_overlay.py", "--show", "--mode", "PANEL", "--run-seconds", "15",
                        "--always-on-top", "--allow-primary"], cwd=ROOT, stdout=f, stderr=subprocess.STDOUT)
time.sleep(5)
img = ImageGrab.grab(all_screens=True)
print("desktop:", img.size)
small = img.copy()
small.thumbnail((1600, 1600))
out = os.path.join(ROOT, "out", "live", "desktop_panel_en.png")
small.save(out)
print("saved", out, small.size)
pid.wait(timeout=40)
