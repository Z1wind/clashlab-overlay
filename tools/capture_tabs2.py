# -*- coding: utf-8 -*-
import ctypes, os, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import ImageGrab
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
X0, Y0, X1, Y1 = 1189, 312, 1629, 1012
u = ctypes.windll.user32
def click(x, y):
    u.SetCursorPos(int(x), int(y)); time.sleep(0.15)
    u.mouse_event(2, 0, 0, 0, 0); time.sleep(0.05); u.mouse_event(4, 0, 0, 0, 0)
    time.sleep(0.9)
def grab(name):
    p = os.path.join(ROOT, "out", "live", name)
    ImageGrab.grab(bbox=(X0, Y0, X1, Y1), all_screens=True).save(p)
    print("saved", name)
grab("tab_research.png")
click(X0 + 135, Y0 + 25); grab("tab_capture.png")
click(X0 + 215, Y0 + 25); grab("tab_layout.png")
click(X0 + 295, Y0 + 25); grab("tab_settings.png")
print("done")
