# -*- coding: utf-8 -*-
import os, re, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import ImageGrab
PY = r"D:\Python313\python.exe"
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
LOG = os.path.join(ROOT, "out", "logs", "hud_target.log")
f = open(LOG, "w", encoding="utf-8")
pid = subprocess.Popen([PY, "run_overlay.py", "--show", "--mode", "HUD", "--run-seconds", "14",
                        "--always-on-top", "--allow-primary"], cwd=ROOT,
                       stdout=f, stderr=subprocess.STDOUT)
time.sleep(5)
f.flush()
txt = open(LOG, encoding="utf-8", errors="replace").read()
m = re.search(r"rect=\((\d+),(\d+),(\d+)x(\d+)\)", txt)
print("rect match:", m.group(0) if m else "none")
if m:
    x, y, w, h = [int(v) for v in m.groups()]
    img = ImageGrab.grab(bbox=(x, y, x + w, y + h), all_screens=True)
    out = os.path.join(ROOT, "out", "live", "hud_target_game.png")
    img.save(out)
    print("saved", out, img.size)
pid.wait(timeout=40)
print("exit", pid.returncode)
