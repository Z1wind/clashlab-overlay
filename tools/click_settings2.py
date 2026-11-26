# -*- coding: utf-8 -*-
import ctypes, os, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import ImageGrab
u = ctypes.windll.user32
u.SetCursorPos(1835, 237)
time.sleep(0.2)
u.mouse_event(2, 0, 0, 0, 0)  # left down
time.sleep(0.05)
u.mouse_event(4, 0, 0, 0, 0)  # left up
time.sleep(0.8)
img = ImageGrab.grab(bbox=(1480, 217, 1920, 937), all_screens=True)
out = os.path.join(r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat", "out", "live", "panel_settings.png")
img.save(out)
print("clicked + saved", out, img.size)
