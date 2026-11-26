# -*- coding: utf-8 -*-
import os, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import ImageGrab
PY = r"D:\Python313\python.exe"
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
pid = subprocess.Popen([PY, "run_overlay.py", "--show", "--mode", "HUD", "--run-seconds", "12",
                        "--always-on-top", "--allow-primary"], cwd=ROOT,
                       stdout=open(os.path.join(ROOT, "out", "logs", "hud_live2.log"), "w"),
                       stderr=subprocess.STDOUT)
time.sleep(5)
img = ImageGrab.grab(bbox=(1956, 307, 1956 + 1280, 307 + 720), all_screens=True)
out = os.path.join(ROOT, "out", "live", "hud_arrow_game.png")
img.save(out)
print("saved", out, img.size)
pid.wait(timeout=40)
print("exit", pid.returncode)
