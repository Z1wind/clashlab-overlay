# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import win32gui
rows = []
def cb(h, _):
    if not win32gui.IsWindowVisible(h):
        return True
    cls = win32gui.GetClassName(h)
    title = win32gui.GetWindowText(h) or ""
    l, t, r, b = win32gui.GetWindowRect(h)
    if "ClashLab" in title or "GLFW" in cls:
        rows.append((cls, title, l, t, r - l, b - t))
    return True
win32gui.EnumWindows(cb, None)
for r in rows:
    print(r)
