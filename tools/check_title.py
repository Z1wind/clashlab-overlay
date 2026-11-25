# -*- coding: utf-8 -*-
"""实机验证窗口标题：起覆盖层 6s，枚举 GLFW30 窗口标题。"""
import os, subprocess, sys, time
import win32gui
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = subprocess.Popen([r"D:\Python313\python.exe", "-W", "ignore", os.path.join(BASE, "run_overlay.py"),
                      "--show", "--mode", "HUD", "--always-on-top", "--allow-primary", "--run-seconds", "8"],
                     cwd=BASE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(4)
titles = []
def cb(h, _):
    cls = win32gui.GetClassName(h)
    if "GLFW" in cls:
        titles.append((cls, win32gui.GetWindowText(h)))
win32gui.EnumWindows(cb, None)
print("glfw windows:", titles)
p.wait(timeout=30)
print("overlay exit:", p.returncode)
