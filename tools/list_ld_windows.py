# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import win32gui
def cb(h, _):
    if win32gui.GetClassName(h) == "LDPlayerMainFrame" and win32gui.IsWindowVisible(h):
        print(h, repr(win32gui.GetWindowText(h)), win32gui.GetWindowRect(h))
    return True
win32gui.EnumWindows(cb, None)
