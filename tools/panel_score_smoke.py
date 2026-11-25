# -*- coding: utf-8 -*-
"""PANEL 冒烟：临时放 layout_current.json（03 阵），跑覆盖层 PANEL 模式并截图，结束后清理。"""
import os, shutil, subprocess, time, json
from PIL import ImageGrab

BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
src = os.path.join(BASE, "bases", "th16", "03", "layout.json")
dst = os.path.join(BASE, "layouts", "layout_current.json")
had = os.path.exists(dst)
if had:
    shutil.copy2(dst, dst + ".bak_smoke")
shutil.copy2(src, dst)
print("layout_current ready", os.path.getsize(dst), "B")

PY = r"D:\Python313\python.exe"
p = subprocess.Popen([PY, "-W", "ignore", os.path.join(BASE, "run_overlay.py"), "--show", "--mode", "PANEL",
                      "--always-on-top", "--allow-primary", "--run-seconds", "12"], cwd=BASE,
                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
time.sleep(6)
ImageGrab.grab().save(os.path.join(BASE, "out", "overlay", "_p3b", "panel_score_t6.png"))
time.sleep(4)
ImageGrab.grab().save(os.path.join(BASE, "out", "overlay", "_p3b", "panel_score_t10.png"))
try:
    out, _ = p.communicate(timeout=25)
except subprocess.TimeoutExpired:
    p.kill(); out, _ = p.communicate()
open(os.path.join(BASE, "out", "overlay", "_p3b", "panel_score_stdout.txt"), "wb").write(out or b"")
print("overlay exit", p.returncode, "stdout", len(out or b""))

# 清理临时 layout
if had:
    shutil.move(dst + ".bak_smoke", dst)
else:
    os.remove(dst)
print("cleaned; layout_current exists now:", os.path.exists(dst))
