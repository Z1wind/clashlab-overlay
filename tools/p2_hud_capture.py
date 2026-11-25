# -*- coding: utf-8 -*-
"""P2：起覆盖层（可见 HUD）→ 桌面抓图 → 结束，全程记录。"""
import sys, os, time, json, subprocess
from PIL import ImageGrab

BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(BASE, "out", "overlay", "_p2")
os.makedirs(OUT, exist_ok=True)
PY = r"D:\Python313\python.exe"

cmd = [PY, "-W", "ignore", os.path.join(BASE, "run_overlay.py"), "--show", "--mode", "HUD",
       "--always-on-top", "--run-seconds", "18"]
p = subprocess.Popen(cmd, cwd=BASE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
time.sleep(6)
ImageGrab.grab().save(os.path.join(OUT, "hud_t6.png"))
time.sleep(4)
ImageGrab.grab().save(os.path.join(OUT, "hud_t10.png"))
time.sleep(4)
ImageGrab.grab().save(os.path.join(OUT, "hud_t14.png"))
try:
    out, _ = p.communicate(timeout=20)
except subprocess.TimeoutExpired:
    p.kill(); out, _ = p.communicate()
txt = (out or b"").decode("utf-8", "ignore")
open(os.path.join(OUT, "overlay_stdout.txt"), "w", encoding="utf-8").write(txt)
print("exit", p.returncode)
print("stdout_len", len(txt))
print(txt[-1200:])
