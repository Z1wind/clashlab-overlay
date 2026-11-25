# -*- coding: utf-8 -*-
"""只读式把雷电主窗提到前台（仅窗口 z 序/焦点，不向游戏发任何输入）。"""
import ctypes, sys
import win32gui, win32con
main = [None]
def _cb(h, _):
    if win32gui.GetClassName(h) == "LDPlayerMainFrame" and win32gui.IsWindowVisible(h):
        main[0] = h
win32gui.EnumWindows(_cb, None)
if not main[0]:
    print("LD not found"); sys.exit(1)
h = main[0]
win32gui.ShowWindow(h, win32con.SW_RESTORE)
# 允许前台切换：附加到前台线程输入队列
fg = ctypes.windll.user32.GetForegroundWindow()
tid_fg = ctypes.windll.user32.GetWindowThreadProcessId(fg, None)
tid_me = ctypes.windll.kernel32.GetCurrentThreadId()
ctypes.windll.user32.AttachThreadInput(tid_fg, tid_me, True)
try:
    win32gui.SetForegroundWindow(h)
except Exception as e:
    print("setfg warn", e)
ctypes.windll.user32.AttachThreadInput(tid_fg, tid_me, False)
win32gui.BringWindowToTop(h)
print("focus requested", int(h), win32gui.GetWindowText(h))
