# -*- coding: utf-8 -*-
import ctypes, os, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import ImageGrab
import win32gui
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
win = None
def cb(h, _):
    global win
    if win is None and win32gui.IsWindowVisible(h) and win32gui.GetClassName(h) == "GLFW30":
        l, t, r, b = win32gui.GetWindowRect(h)
        if abs((r - l) - 440) <= 12:
            win = (h, l, t, r, b)
    return True
win32gui.EnumWindows(cb, None)
print("win:", win)
if win:
    h, x0, y0, x1, y1 = win
    u = ctypes.windll.user32
    def click(px, py):
        u.SetCursorPos(int(x0 + px), int(y0 + py)); time.sleep(0.25)
        u.mouse_event(2, 0, 0, 0, 0); time.sleep(0.1); u.mouse_event(4, 0, 0, 0, 0)
        time.sleep(1.2)
    click(220, 600)   # 先点空白激活窗口
    click(52, 25)     # 研究
    p = os.path.join(ROOT, "out", "live", "research_final2.png")
    ImageGrab.grab(bbox=(x0, y0, x1, y1), all_screens=True).save(p)
    print("saved", p)
