# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "overlay", "pages.py")
t = open(p, encoding="utf-8").read()
old = '''    if not isinstance(payload, dict):
        return "对手：未识别（F6）"
    line = payload.get("line")'''
new = '''    if not isinstance(payload, dict) or not payload:
        return "对手：未识别（F6）"
    line = payload.get("line")'''
if old in t:
    t = t.replace(old, new, 1)
    old2 = '''    th = payload.get("th")
    ocr = payload.get("ocr") or {}
    name = ocr.get("name") or "未知"'''
    new2 = '''    th = payload.get("th")
    ocr = payload.get("ocr") or {}
    if not th and not ocr.get("name"):
        return "对手：未识别（F6）"
    name = ocr.get("name") or "未知"'''
    t = t.replace(old2, new2, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("fmt fixed")
else:
    print("anchor miss")
