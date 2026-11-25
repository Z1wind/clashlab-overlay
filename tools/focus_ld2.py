# -*- coding: utf-8 -*-
"""ALT 解锁前台权 -> 把雷电主窗提到前台（窗口级，不向游戏发业务输入）。"""
import ctypes, time, sys
import win32gui, win32con
from ctypes import wintypes

main = [None]
def _cb(h, _):
    if win32gui.GetClassName(h) == "LDPlayerMainFrame" and win32gui.IsWindowVisible(h):
        main[0] = h
win32gui.EnumWindows(_cb, None)
if not main[0]:
    print("LD not found"); sys.exit(1)
h = main[0]

KEYEVENTF_KEYUP = 0x0002
VK_MENU = 0x12
INPUT_KEYBOARD = 1
class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]
class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("ki", KEYBDINPUT)]
def alt(up):
    inp = INPUT(); inp.type = INPUT_KEYBOARD
    inp.ki = KEYBDINPUT(VK_MENU, 0, KEYEVENTF_KEYUP if up else 0, 0, None)
    ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))

alt(False); time.sleep(0.05); alt(True)
time.sleep(0.1)
win32gui.ShowWindow(h, win32con.SW_RESTORE)
ok = win32gui.SetForegroundWindow(h)
time.sleep(0.3)
fg = ctypes.windll.user32.GetForegroundWindow()
print("setfg", ok, "fg_match", int(fg) == int(h), "fg_title", win32gui.GetWindowText(fg))
