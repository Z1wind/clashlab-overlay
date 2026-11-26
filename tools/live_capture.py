# -*- coding: utf-8 -*-
import os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import win32gui, win32ui, win32con
from PIL import Image
os.makedirs(r"out\live", exist_ok=True)

def capture(hwnd, path):
    left, top, right, bot = win32gui.GetWindowRect(hwnd)
    w, h = right - left, bot - top
    hwndDC = win32gui.GetWindowDC(hwnd)
    mfcDC = win32ui.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()
    bmp = win32ui.CreateBitmap()
    bmp.CreateCompatibleBitmap(mfcDC, w, h)
    saveDC.SelectObject(bmp)
    saveDC.BitBlt((0, 0), (w, h), mfcDC, (0, 0), win32con.SRCCOPY)
    bmp.SaveBitmapFile(saveDC, path)
    win32gui.DeleteObject(bmp.GetHandle())
    saveDC.DeleteDC(); mfcDC.DeleteDC(); win32gui.ReleaseDC(hwnd, hwndDC)
    return path, w, h

for hwnd, name in ((2097582, "ld_main"), (1838514, "ld_1")):
    try:
        p, w, h = capture(hwnd, r"out\live\%s.png" % name)
        print(name, hwnd, w, "x", h, "->", p)
    except Exception as e:
        print(name, "ERR", str(e)[:100])
