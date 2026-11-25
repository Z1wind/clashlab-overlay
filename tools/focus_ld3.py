# -*- coding: utf-8 -*-
"""P2 抢前台：三级强度，成功即停；全程不发键盘事件。
① SwitchToThisWindow ② AttachThreadInput+SetForegroundWindow ③ SetWindowPos TOPMOST 顶置。"""
import ctypes, time, sys
import win32gui, win32con

main=[None]
def _cb(h,_):
    if win32gui.GetClassName(h)=="LDPlayerMainFrame" and win32gui.IsWindowVisible(h):
        main[0]=h
win32gui.EnumWindows(_cb,None)
if not main[0]:
    print("LD not found"); sys.exit(1)
h=main[0]
u=ctypes.windll.user32

def fg_match():
    return int(u.GetForegroundWindow())==int(h)

# ① SwitchToThisWindow
win32gui.ShowWindow(h, win32con.SW_RESTORE)
u.SwitchToThisWindow(h, True)
time.sleep(0.6)
if fg_match():
    print("TIER1 SwitchToThisWindow OK"); sys.exit(0)
print("TIER1 fail")

# ② AttachThreadInput + SetForegroundWindow
fg=u.GetForegroundWindow()
tid_fg=u.GetWindowThreadProcessId(fg,None)
tid_me=ctypes.windll.kernel32.GetCurrentThreadId()
u.AttachThreadInput(tid_fg,tid_me,True)
try:
    win32gui.SetForegroundWindow(h)
except Exception as e:
    print("setfg exc",e)
u.AttachThreadInput(tid_fg,tid_me,False)
time.sleep(0.6)
if fg_match():
    print("TIER2 AttachThreadInput+SetForegroundWindow OK"); sys.exit(0)
print("TIER2 fail")

# ③ SetWindowPos TOPMOST 顶一下再 NOTOPMOST
u.SetWindowPos(h, win32con.HWND_TOPMOST, 0,0,0,0,
               win32con.SWP_NOMOVE|win32con.SWP_NOSIZE|win32con.SWP_SHOWWINDOW)
time.sleep(0.3)
u.SetWindowPos(h, win32con.HWND_NOTOPMOST, 0,0,0,0,
               win32con.SWP_NOMOVE|win32con.SWP_NOSIZE|win32con.SWP_SHOWWINDOW)
time.sleep(0.6)
if fg_match():
    print("TIER3 topmost-toggle OK"); sys.exit(0)
print("TIER3 fail; fg=",win32gui.GetWindowText(u.GetForegroundWindow()))
