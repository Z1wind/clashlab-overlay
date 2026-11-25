# -*- coding: utf-8 -*-
"""只读抓屏：保存全屏到 out/overlay/<name>.png。不点击、不按键。"""
import sys, os
ROOT = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
name = sys.argv[1] if len(sys.argv) > 1 else "grab.png"
dst = os.path.join(ROOT, "out", "overlay", name)
try:
    from PIL import ImageGrab
    img = ImageGrab.grab(all_screens=True)
    img.save(dst)
except Exception as e:
    import mss
    with mss.mss() as sct:
        mon = sct.monitors[0]
        sct.shot(mon=mon, output=dst)
print("saved", dst)
