# -*- coding: utf-8 -*-
import os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import ImageGrab
PY = r"D:\Python313\python.exe"
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
pid = subprocess.Popen([PY, "run_overlay.py", "--show", "--mode", "HUD", "--run-seconds", "10",
                        "--always-on-top", "--allow-primary"], cwd=ROOT,
                       stdout=open(os.path.join(ROOT, "out", "logs", "hud_live.log"), "w"),
                       stderr=subprocess.STDOUT)
time.sleep(4)
img = ImageGrab.grab(bbox=(94, 237, 1130, 832), all_screens=True)
out = os.path.join(ROOT, "out", "live", "hud_arrow_desktop.png")
img.save(out)
print("saved", out, img.size)
pid.wait(timeout=30)
print("overlay exit", pid.returncode)
