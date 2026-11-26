# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "overlay", "runtime.py")
t = open(p, encoding="utf-8").read()
if "ClashLabOverlaySingleton" not in t:
    anchor = "def run(root: str, config: dict | None = None) -> None:"
    helper = '''def _single_instance_guard() -> bool:
    """命名互斥：一台机器只允许一个覆盖层实例（多例会互相抢窗口/尺寸错乱）。"""
    try:
        import ctypes
        k32 = ctypes.windll.kernel32
        k32.CreateMutexW(None, False, "Global\\\\ClashLabOverlaySingleton")
        return k32.GetLastError() != 183  # ERROR_ALREADY_EXISTS
    except Exception:
        return True


'''
    t = t.replace(anchor, helper + anchor, 1)
    start = '    rt = _Runtime(root, cfg)\n    rt.log("overlay runtime start")'
    new = ('    rt = _Runtime(root, cfg)\n'
           '    rt.log("overlay runtime start")\n'
           '    if not _single_instance_guard():\n'
           '        rt.log("another ClashLab overlay is already running; exit this instance")\n'
           '        return')
    if start in t:
        t = t.replace(start, new, 1)
        print("singleton guard added")
    else:
        print("start marker miss")
else:
    print("already")
open(p, "w", encoding="utf-8", newline="\n").write(t)
