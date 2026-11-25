# -*- coding: utf-8 -*-
"""只读：LDPlayerMainFrame 窗口状态（rect/可见/最小化/前台）+ 顶层窗口 z 序前 12。"""
import ctypes, json
import win32gui, win32con
out = {"ld": None, "top": []}
main = [None]
def _cb(h, _):
    if win32gui.GetClassName(h) == "LDPlayerMainFrame" and win32gui.IsWindowVisible(h):
        main[0] = h
win32gui.EnumWindows(_cb, None)
if main[0]:
    h = main[0]
    r = win32gui.GetWindowRect(h)
    out["ld"] = {
        "hwnd": int(h), "title": win32gui.GetWindowText(h),
        "rect": list(r), "visible": bool(win32gui.IsWindowVisible(h)),
        "minimized": bool(win32gui.IsIconic(h)),
        "foreground": int(ctypes.windll.user32.GetForegroundWindow()) == int(h),
    }
# z 序顶层可见窗口
order = []
def _enum(h, _):
    if win32gui.IsWindowVisible(h):
        order.append((int(h), win32gui.GetClassName(h), win32gui.GetWindowText(h)[:40]))
win32gui.EnumWindows(_enum, None)
out["top"] = order[:15]
print(json.dumps(out, ensure_ascii=False, indent=2))
