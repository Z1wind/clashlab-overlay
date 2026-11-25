# -*- coding: utf-8 -*-
import os, subprocess, time
import win32gui
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = subprocess.Popen([r"D:\Python313\python.exe", "-W", "ignore", os.path.join(BASE, "run_overlay.py"),
                      "--show", "--mode", "HUD", "--always-on-top", "--allow-primary", "--run-seconds", "6"],
                     cwd=BASE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(3)
titles = []
def cb(h, _):
    if "GLFW" in win32gui.GetClassName(h):
        titles.append(win32gui.GetWindowText(h))
win32gui.EnumWindows(cb, None)
for t in titles:
    print("title codepoints:", [hex(ord(c)) for c in t], "| expected:", [hex(ord(c)) for c in "ClashLab 覆盖层"], "| equal:", t == "ClashLab 覆盖层")
p.wait(timeout=30)
print("exit:", p.returncode)
