# -*- coding: utf-8 -*-
import os, sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import ImageGrab
try:
    import pyautogui
    pyautogui.click(1835, 237)  # 设置 tab（面板内第 4 个）
    time.sleep(0.8)
    print("clicked settings tab")
except Exception as e:
    print("click fail:", e)
img = ImageGrab.grab(bbox=(1480, 217, 1920, 937), all_screens=True)
out = os.path.join(r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat", "out", "live", "panel_settings.png")
img.save(out)
print("saved", out)
