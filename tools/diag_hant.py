# -*- coding: utf-8 -*-
import sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
sys.path.insert(0, BASE)
try:
    import zhconv
    print("zhconv OK", zhconv.convert("阵型 采集 设置 阵型未加载/点采集", "zh-hant"))
except Exception as e:
    print("zhconv FAIL:", repr(e))
from clashlab.overlay import lang
print("to_hant:", lang.to_hant("阵型 采集 设置 面板 实时"))
print("set:", lang.set(BASE, "zh-hant"), "get:", lang.get(), "to_hant now:", lang.to_hant("阵型"))
