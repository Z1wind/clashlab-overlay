# -*- coding: utf-8 -*-
"""P2 实机：恢复雷电窗口 → 起覆盖层 → 抓桌面 → 记录几何。"""
import sys, os, time, json, subprocess
import win32gui, win32con
from PIL import ImageGrab

BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
OUT = os.path.join(BASE, "out", "overlay", "_p2")
os.makedirs(OUT, exist_ok=True)

h = win32gui.FindWindow("LDPlayerMainFrame", None)
print("main hwnd", h)
win32gui.ShowWindow(h, win32con.SW_RESTORE)
time.sleep(1.2)
rect = win32gui.GetWindowRect(h)
print("main rect", rect)
kids = []
def walk(hwnd, out):
    c = None
    while True:
        c = win32gui.FindWindowEx(hwnd, c, None, None)
        if not c:
            break
        out.append((c, win32gui.GetClassName(c), win32gui.GetWindowText(c), win32gui.GetWindowRect(c)))
        walk(c, out)
walk(h, kids)
render = [k for k in kids if "Render" in k[1] or "TheRender" in k[2]]
print("render children", render[:3])
json.dump({"main": [h, rect], "render": render}, open(os.path.join(OUT, "geom.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
