# -*- coding: utf-8 -*-
import os, re, subprocess, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import ImageGrab
PY = r"D:\Python313\python.exe"
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
LOG = os.path.join(ROOT, "out", "logs", "panel_en5.log")
f = open(LOG, "w", encoding="utf-8")
pid = subprocess.Popen([PY, "-u", "run_overlay.py", "--show", "--mode", "PANEL", "--lang", "en",
                        "--run-seconds", "16", "--always-on-top", "--allow-primary"],
                       cwd=ROOT, stdout=f, stderr=subprocess.STDOUT)
time.sleep(7)
f.flush()
txt = open(LOG, encoding="utf-8", errors="replace").read()
print("draw errors:", txt.count("draw_panel error"))
m = re.search(r"rect=\((\d+),(\d+),(\d+)x(\d+)\)", txt)
print("rect:", m.group(0) if m else "none")
if m:
    x, y, w, h = [int(v) for v in m.groups()]
    img = ImageGrab.grab(bbox=(x, y, x + w, y + h), all_screens=True)
    out = os.path.join(ROOT, "out", "live", "panel_en_verified.png")
    img.save(out)
    print("saved", out, img.size)
pid.wait(timeout=40)
