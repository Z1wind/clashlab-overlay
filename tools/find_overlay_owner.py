# -*- coding: utf-8 -*-
"""找 clashlab-overlay 窗口属主 PID/进程名，打印供处置。"""
import ctypes, json
import win32gui, win32api, win32process
hits=[]
def _cb(h,_):
    t=win32gui.GetWindowText(h)
    if "overlay" in t.lower():
        pid=ctypes.c_uint(); tid=ctypes.windll.user32.GetWindowThreadProcessId(h, ctypes.byref(pid))
        hits.append({"hwnd":int(h),"title":t,"cls":win32gui.GetClassName(h),
                     "pid":pid.value,"visible":bool(win32gui.IsWindowVisible(h))})
win32gui.EnumWindows(_cb,None)
for x in hits:
    try:
        import subprocess
        p=win32api.OpenProcess(0x1000,False,x["pid"])
        x["exe"]=win32process.GetModuleFileNameEx(p,0)
        win32api.CloseHandle(p)
    except Exception as e:
        x["exe_err"]=str(e)
print(json.dumps(hits,ensure_ascii=False,indent=1))
