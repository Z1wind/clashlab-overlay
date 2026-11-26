# -*- coding: utf-8 -*-
"""Lead 侧独立实机冒烟：PANEL + 布局，截图，恢复布局文件。"""
import os, shutil, subprocess, sys, time
from PIL import ImageGrab
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
LAY = os.path.join(BASE, "layouts", "layout_current.json")
SRC = os.path.join(BASE, "bases", "th16", "03", "layout.json")
had = os.path.exists(LAY)
if had:
    shutil.copy2(LAY, LAY + ".lead_bak")
shutil.copy2(SRC, LAY)
p = subprocess.Popen([r"D:\Python313\python.exe", "-u", os.path.join(BASE, "run_overlay.py"),
                      "--show", "--mode", "PANEL", "--always-on-top", "--allow-primary", "--run-seconds", "8"],
                     cwd=BASE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
time.sleep(5)
shot = os.path.join(BASE, "out", "qa_e2e", "lead_panel_shot.png")
ImageGrab.grab().save(shot)
try:
    out, _ = p.communicate(timeout=30)
except subprocess.TimeoutExpired:
    p.kill(); out, _ = p.communicate()
log = (out or b"").decode("utf-8", "ignore")
if had:
    shutil.move(LAY + ".lead_bak", LAY)
else:
    os.remove(LAY)
print("exit:", p.returncode, "| shot:", os.path.getsize(shot), "B")
for line in log.splitlines():
    if any(k in line for k in ("mode=", "fps summary", "runtime end", "Traceback", "score", "panel")):
        print("LOG:", line[:160])
