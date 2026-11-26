# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import ImageGrab
p = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat\out\live\exe_panel_final.png"
ImageGrab.grab(bbox=(1200, 301, 1640, 1001), all_screens=True).save(p)
print("saved", p)
