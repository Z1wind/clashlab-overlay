# -*- coding: utf-8 -*-
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from PIL import ImageGrab
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
img = ImageGrab.grab(bbox=(1480, 217, 1920, 937), all_screens=True)
out = os.path.join(ROOT, "out", "live", "panel_now.png")
img.save(out)
print("saved", out, img.size)
