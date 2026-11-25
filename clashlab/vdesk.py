# -*- coding: utf-8 -*-
"""虚拟桌面：把采集与 HUD 放到独立的 Windows 桌面上运行。

物理桌面保持不动，鼠标位置与前台窗口不变，测试过程不会抢鼠标。
输入走 ADB，本来就不经过 Windows 输入栈，两层保险。
"""
import ctypes
import os
import subprocess
import sys
import json

from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)
user32.CreateDesktopW.restype = wintypes.HANDLE
user32.CreateDesktopW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.LPVOID,
                                  wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID]
user32.CloseDesktop.argtypes = [wintypes.HANDLE]

GENERIC_ALL = 0x10000000


class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


def cursor_pos():
    p = POINT()
    user32.GetCursorPos(ctypes.byref(p))
    return (p.x, p.y)


def foreground_hwnd():
    return int(user32.GetForegroundWindow())


def create_desktop(name="ClashLabBench"):
    h = user32.CreateDesktopW(name, None, None, 0, GENERIC_ALL, None)
    if not h:
        raise OSError(f"创建桌面失败：{ctypes.get_last_error()}")
    return h


def spawn_on_desktop(hdesk_name, args, cwd=None):
    si = subprocess.STARTUPINFO()
    si.lpDesktop = f"WinSta0\\{hdesk_name}"
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = 0  # SW_HIDE
    return subprocess.Popen(args, cwd=cwd, startupinfo=si,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)


def run_bench(seconds=10, serial="", adb="", out="out/bench", cwd=None, desktop_name="ClashLabBench",
              recover=False, layout=""):
    """在新桌面上跑一遍真实采集 + HUD，并校验物理桌面未被干扰。"""
    before_cursor = cursor_pos()
    before_fg = foreground_hwnd()

    hdesk = create_desktop(desktop_name)
    result = {"desktop": desktop_name, "desktop_handle": hex(int(hdesk)),
              "cursor_before": before_cursor, "foreground_before": hex(before_fg)}

    cmd = [sys.executable, "-m", "clashlab", "run",
           "--seconds", str(seconds), "--hud", "--out", out]
    if recover:
        cmd += ["--recover"]
    if layout:
        cmd += ["--layout", layout]
    if serial:
        cmd += ["--serial", serial]
    if adb:
        cmd += ["--adb", adb]

    child = spawn_on_desktop(desktop_name, cmd, cwd=cwd or os.getcwd())
    try:
        stdout, _ = child.communicate(timeout=seconds + 60)
        result["child_exit"] = child.returncode
        result["child_log"] = (stdout or b"").decode("utf-8", "ignore")[-2000:]
    except subprocess.TimeoutExpired:
        child.kill()
        result["child_exit"] = "timeout"
        result["child_log"] = "子进程超时被终止"

    result["cursor_after"] = cursor_pos()
    result["foreground_after"] = hex(foreground_hwnd())
    result["cursor_unchanged"] = result["cursor_before"] == result["cursor_after"]
    result["foreground_unchanged"] = result["foreground_before"] == result["foreground_after"]

    try:
        user32.CloseDesktop(hdesk)
    except Exception:
        pass

    rp = os.path.join(out, "report.json")
    if os.path.exists(rp):
        with open(rp, "r", encoding="utf-8") as f:
            result["child_report"] = json.load(f)
    return result
