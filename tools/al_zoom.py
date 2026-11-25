# -*- coding: utf-8 -*-
"""滚轮缩放尝试 v2：不抢前台，只移动光标到窗口内再滚。"""
import sys, time
import win32gui, win32con, win32api

CLS = "LDPlayerMainFrame"


def main(times=6, delta=120):
    h = win32gui.FindWindow(CLS, None)
    win32gui.ShowWindow(h, win32con.SW_RESTORE)
    time.sleep(1.2)
    rect = win32gui.GetWindowRect(h)
    print("rect", rect)
    l, t, r, b = rect
    cx, cy = (l + r) // 2, (t + b) // 2
    print("center", cx, cy)
    win32api.SetCursorPos((cx, cy))
    time.sleep(0.4)
    for _ in range(times):
        win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, delta, 0)
        time.sleep(0.3)
    print("done")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 6)
