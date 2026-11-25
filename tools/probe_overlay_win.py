# -*- coding: utf-8 -*-
"""运行中探测 clashlab-overlay 窗口：GetWindowRect/尺寸/WS_EX_TOPMOST；只读。"""
import ctypes, json
import win32gui, win32con
hits=[]
def _cb(h,_):
    if win32gui.GetWindowText(h)=="clashlab-overlay":
        r=win32gui.GetWindowRect(h)
        ex=win32gui.GetWindowLong(h,win32con.GWL_EXSTYLE)
        hits.append({"hwnd":int(h),"rect":list(r),
                     "size":[r[2]-r[0],r[3]-r[1]],
                     "topmost":bool(ex&win32con.WS_EX_TOPMOST),
                     "exstyle":hex(ex),"visible":bool(win32gui.IsWindowVisible(h))})
win32gui.EnumWindows(_cb,None)
print(json.dumps(hits,ensure_ascii=False,indent=1))
