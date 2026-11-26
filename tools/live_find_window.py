# -*- coding: utf-8 -*-
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import win32gui, win32ui, win32con
from PIL import Image

def windows():
    out = []
    def cb(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            t = win32gui.GetWindowText(hwnd)
            cls = win32gui.GetClassName(hwnd)
            if t and any(k in t.lower() or k in cls.lower() for k in ("ld", "雷电", "clash", "coc", "player")):
                out.append((hwnd, t, cls, win32gui.GetWindowRect(hwnd)))
    win32gui.EnumWindows(cb, None)
    return out

wins = windows()
for w in wins[:10]:
    print(w)
if not wins:
    print("no candidate window")
