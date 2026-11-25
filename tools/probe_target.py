# -*- coding: utf-8 -*-
"""P2 前置只读探针：定位 LDPlayerMainFrame 渲染子窗口，报客户区原点/尺寸/exstyle/主屏。
不点鼠标、不按键、不修改任何窗口。期望：客户区原点(201,195)、1002x563。"""
import ctypes, json, sys
import win32gui, win32con, win32api

out = {"main": None, "children": [], "monitor_primary": None}
main = [None]
def _cb(h, _):
    if win32gui.GetClassName(h) == "LDPlayerMainFrame" and win32gui.IsWindowVisible(h):
        main[0] = h
win32gui.EnumWindows(_cb, None)
out["main"] = main[0]
if not main[0]:
    out["error"] = "LDPlayerMainFrame not found"
    print(json.dumps(out, ensure_ascii=False, indent=2)); sys.exit(0)

best = [None, 0]
def _walk(h, depth=0):
    kids = []
    win32gui.EnumChildWindows(h, lambda k, _: kids.append(k), None)
    for k in kids:
        if win32gui.IsWindowVisible(k):
            r = win32gui.GetClientRect(k)
            area = r[2]*r[3]
            if area > best[1]:
                best[0], best[1] = k, area
            pt = win32gui.ClientToScreen(k, (0, 0))
            ex = win32gui.GetWindowLong(k, win32con.GWL_EXSTYLE)
            out["children"].append({
                "hwnd": int(k), "cls": win32gui.GetClassName(k),
                "client_origin": list(pt), "client_size": [r[2], r[3]],
                "exstyle": hex(ex), "topmost": bool(ex & win32con.WS_EX_TOPMOST),
                "area": area,
            })
        _walk(k, depth+1)
_walk(main[0])

# 主屏判定
hmon = ctypes.windll.user32.MonitorFromWindow(best[0], 0)
class MI(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint), ("rcMonitor", ctypes.c_long*4),
                ("rcWork", ctypes.c_long*4), ("dwFlags", ctypes.c_uint)]
mi = MI(); mi.cbSize = ctypes.sizeof(MI)
ctypes.windll.user32.GetMonitorInfoW(hmon, ctypes.byref(mi))
out["monitor_primary"] = bool(mi.dwFlags & 1)
out["monitor_rc"] = list(mi.rcMonitor)
out["best_child"] = {k: v for k, v in out["children"][-1].items()} if out["children"] else None
# 校验
if best[0]:
    pt = win32gui.ClientToScreen(best[0], (0,0)); r = win32gui.GetClientRect(best[0])
    out["check"] = {
        "origin_match": pt == (201, 195), "size_match": (r[2], r[3]) == (1002, 563),
        "got": {"origin": list(pt), "size": [r[2], r[3]]},
        "expected": {"origin": [201, 195], "size": [1002, 563]},
    }
print(json.dumps(out, ensure_ascii=False, indent=2))
