# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"

# 1) 单实例互斥：runtime.run 开头加 named mutex
p = os.path.join(BASE, "clashlab", "overlay", "runtime.py")
t = open(p, encoding="utf-8").read()
if "ClashLabOverlaySingleton" not in t:
    anchor = "def run(root, cfg=None):"
    add = '''def _single_instance_guard() -> bool:
    """命名互斥：同一台机器只允许一个覆盖层实例，避免多实例互相抢窗口/尺寸错乱。"""
    try:
        import ctypes
        k32 = ctypes.windll.kernel32
        k32.CreateMutexW(None, False, "Global\\\\ClashLabOverlaySingleton")
        return k32.GetLastError() != 183  # ERROR_ALREADY_EXISTS
    except Exception:
        return True


def run(root, cfg=None):'''
    if anchor in t:
        t = t.replace(anchor, add, 1)
        # 在 run 内部最早记录日志处插入检查
        marker = "    rt.log(\"overlay runtime start\")"
        if marker in t:
            t = t.replace(marker, "    if not _single_instance_guard():\n        try:\n            rt.log(\"another ClashLab overlay is already running; exit this instance\")\n        except Exception:\n            pass\n        return\n" + marker, 1)
            print("singleton guard added")
        else:
            print("runtime start marker miss")
    else:
        print("run anchor miss")
open(p, "w", encoding="utf-8", newline="\n").write(t)
