# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "push_changes.py")
t = open(p, encoding="utf-8").read()
old = 'git = os.path.join(os.environ.get("TEMP", ""), "gitportable", "mingit", "cmd", "git.exe")'
new = '''_CANDIDATES = [
    os.path.join(os.environ.get("TEMP", ""), "mingit2", "cmd", "git.exe"),
    os.path.join(os.environ.get("TEMP", ""), "gitportable", "mingit", "cmd", "git.exe"),
    r"E:\\Temp\\mingit2\\cmd\\git.exe",
    r"C:\\Program Files\\Git\\cmd\\git.exe",
]
git = next((c for c in _CANDIDATES if os.path.exists(c)), _CANDIDATES[0])'''
if old in t:
    t = t.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("git path resolver patched")
else:
    print("anchor miss")
