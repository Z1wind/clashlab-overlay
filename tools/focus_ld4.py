# -*- coding: utf-8 -*-
"""P2 抢前台补档：LockSetForegroundWindow 解锁 + 多手法重试；无键盘事件。"""
import ctypes, time, sys
import win32gui, win32con
u=ctypes.windll.user32

main=[None]
def _cb(h,_):
    if win32gui.GetClassName(h)=="LDPlayerMainFrame" and win32gui.IsWindowVisible(h):
        main[0]=h
win32gui.EnumWindows(_cb,None)
if not main[0]:
    print("LD not found"); sys.exit(1)
h=main[0]

# LSFW_UNLOCK = 2
try:
    u.LockSetForegroundWindow(2, 0)
except Exception as e:
    print("unlock exc",e)
time.sleep(0.2)

def fg_match(): return int(u.GetForegroundWindow())==int(h)

# A: SwitchToThisWindow
win32gui.ShowWindow(h, win32con.SW_RESTORE)
u.SwitchToThisWindow(h, True); time.sleep(0.5)
if fg_match(): print("A SwitchToThisWindow OK"); sys.exit(0)

# B: attach fg thread + setfg
fg=u.GetForegroundWindow()
tid_fg=u.GetWindowThreadProcessId(fg,None)
tid_me=ctypes.windll.kernel32.GetCurrentThreadId()
u.AttachThreadInput(tid_fg,tid_me,True)
try: win32gui.SetForegroundWindow(h)
except Exception as e: print("B exc",e)
u.AttachThreadInput(tid_fg,tid_me,False)
time.sleep(0.5)
if fg_match(): print("B Attach+SetFG OK"); sys.exit(0)

# C: topmost toggle
u.SetWindowPos(h, win32con.HWND_TOPMOST,0,0,0,0,win32con.SWP_NOMOVE|win32con.SWP_NOSIZE|win32con.SWP_SHOWWINDOW)
time.sleep(0.3)
u.SetWindowPos(h, win32con.HWND_NOTOPMOST,0,0,0,0,win32con.SWP_NOMOVE|win32con.SWP_NOSIZE|win32con.SWP_SHOWWINDOW)
time.sleep(0.5)
if fg_match(): print("C topmost-toggle OK"); sys.exit(0)

print("ALL FAIL; fg=", win32gui.GetWindowText(u.GetForegroundWindow()))
