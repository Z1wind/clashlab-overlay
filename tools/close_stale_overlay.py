# -*- coding: utf-8 -*-
"""关闭残留 clashlab-overlay 窗口（本应用自身窗口，WM_CLOSE 优雅关闭）。"""
import ctypes, json
import win32gui, win32con
hits=[]
def _cb(h,_):
    t=win32gui.GetWindowText(h)
    if "clashlab-overlay" in t.lower() or t=="clashlab-overlay":
        hits.append((h,t,win32gui.GetClassName(h),win32gui.IsWindowVisible(h)))
win32gui.EnumWindows(_cb,None)
for h,t,cls,vis in hits:
    print("close",h,cls,repr(t),"visible",vis)
    win32gui.PostMessage(h, win32con.WM_CLOSE, 0, 0)
print("done",len(hits))
