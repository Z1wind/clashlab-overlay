# -*- coding: utf-8 -*-
import ctypes, os, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import ImageGrab
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
X0, Y0, W, H = 1189, 312, 440, 700
u = ctypes.windll.user32
ImageGrab.grab(bbox=(X0, Y0, X0 + W, Y0 + H), all_screens=True).save(os.path.join(ROOT, "out", "live", "zh_now.png"))
u.SetCursorPos(X0 + 291, Y0 + 25); time.sleep(0.15)
u.mouse_event(2, 0, 0, 0, 0); time.sleep(0.05); u.mouse_event(4, 0, 0, 0, 0)
time.sleep(0.9)
ImageGrab.grab(bbox=(X0, Y0, X0 + W, Y0 + H), all_screens=True).save(os.path.join(ROOT, "out", "live", "zh_settings_now.png"))
print("saved zh_now / zh_settings_now")
