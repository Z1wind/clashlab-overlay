# -*- coding: utf-8 -*-
import ctypes, hashlib, os, sys, time
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
    def click(px):
        u.SetCursorPos(int(x0 + px), int(y0 + 25)); time.sleep(0.15)
        u.mouse_event(2, 0, 0, 0, 0); time.sleep(0.06); u.mouse_event(4, 0, 0, 0, 0)
        time.sleep(0.9)
        img = ImageGrab.grab(bbox=(x0, y0, x1, y1), all_screens=True)
        p = os.path.join(ROOT, "out", "live", "tabtest_%d.png" % px)
        img.save(p)
        return hashlib.md5(img.tobytes()).hexdigest()[:10], p
    for px in (52, 132, 212, 292):
        hsh, p = click(px)
        print(px, "->", p, hsh)
