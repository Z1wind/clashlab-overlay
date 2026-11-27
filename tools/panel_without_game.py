# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "overlay", "runtime.py")
t = open(p, encoding="utf-8").read()
old = '''        if wait:
            if prev.get("wait_shown") is not True:
                win32gui.ShowWindow(hwnd, SW_SHOWNOACTIVATE)
                prev["wait_shown"] = True
                rt.log("waiting: LDPlayerMainFrame 未找到，持续轮询等待启动")
            sw = user32.GetSystemMetrics(0)
            sh = user32.GetSystemMetrics(1)
            wx, wy = int((sw - 420) / 2), int((sh - 90) / 2)
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, wx, wy,
                                  420, 90, win32con.SWP_NOACTIVATE)'''
new = '''        if wait:
            sw = user32.GetSystemMetrics(0)
            sh = user32.GetSystemMetrics(1)
            if rt.state.mode == "PANEL":
                # 没有游戏窗口时面板独立可用（不再只显示小横幅）
                pw = 440
                ph = max(400, min(700, sh - 60))
                wx, wy = sw - pw - 8, 30
                win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, wx, wy, pw, ph,
                                      win32con.SWP_NOACTIVATE | win32con.SWP_SHOWWINDOW)
                if prev.get("wait_shown") is not True:
                    win32gui.ShowWindow(hwnd, SW_SHOWNOACTIVATE)
                    prev["wait_shown"] = True
                    rt.log("waiting: no render target -> PANEL standalone at (%d,%d) %dx%d" % (wx, wy, pw, ph))
            else:
                if prev.get("wait_shown") is not True:
                    win32gui.ShowWindow(hwnd, SW_SHOWNOACTIVATE)
                    prev["wait_shown"] = True
                    rt.log("waiting: LDPlayerMainFrame 未找到，持续轮询等待启动")
                wx, wy = int((sw - 420) / 2), int((sh - 90) / 2)
                win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, wx, wy,
                                      420, 90, win32con.SWP_NOACTIVATE)'''
if old in t:
    t = t.replace(old, new, 1)
    # 绘制分支：PANEL 时画面板
    old2 = '''            if wait:
                _draw_wait_banner(imgui, dl)
            elif rt.state.mode == "PANEL":'''
    new2 = '''            if wait and rt.state.mode != "PANEL":
                _draw_wait_banner(imgui, dl)
            elif rt.state.mode == "PANEL":'''
    if old2 in t:
        t = t.replace(old2, new2, 1)
        print("draw branch patched")
    else:
        print("draw branch miss")
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("runtime wait-panel patched")
else:
    print("anchor miss")
