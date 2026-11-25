# -*- coding: utf-8 -*-
"""把 LD 主窗移回可视区 (200,150)，不发输入、不改尺寸；随后解锁前台+SwitchToThisWindow。"""
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
win32gui.ShowWindow(h, win32con.SW_RESTORE)
# 移动到 (200,150)，保留尺寸
u.SetWindowPos(h, win32con.HWND_TOP, 200,150,0,0,
               win32con.SWP_NOSIZE|win32con.SWP_SHOWWINDOW)
time.sleep(0.4)
# 解锁前台并切换
try: u.LockSetForegroundWindow(2,0)
except Exception as e: print("unlock",e)
u.SwitchToThisWindow(h, True)
time.sleep(0.6)
fg=u.GetForegroundWindow()
print("fg_match=",int(fg)==int(h),"fg=",win32gui.GetWindowText(fg))
r=win32gui.GetWindowRect(h)
print("main_rect=",list(r))
