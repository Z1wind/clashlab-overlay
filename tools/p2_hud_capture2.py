# -*- coding: utf-8 -*-
import os, time, subprocess
from PIL import ImageGrab
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(BASE, "out", "overlay", "_p2")
PY = r"D:\Python313\python.exe"
p = subprocess.Popen([PY, "-W", "ignore", os.path.join(BASE, "run_overlay.py"), "--show", "--mode", "HUD",
                      "--always-on-top", "--allow-primary", "--run-seconds", "16"], cwd=BASE,
                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
time.sleep(6)
ImageGrab.grab().save(os.path.join(OUT, "hudp_t6.png"))
time.sleep(3)
ImageGrab.grab().save(os.path.join(OUT, "hudp_t9.png"))
time.sleep(3)
ImageGrab.grab().save(os.path.join(OUT, "hudp_t12.png"))
try:
    out, _ = p.communicate(timeout=20)
except subprocess.TimeoutExpired:
    p.kill(); out, _ = p.communicate()
open(os.path.join(OUT, "hudp_stdout.txt"), "wb").write(out or b"")
print("exit", p.returncode, "len", len(out or b""))
