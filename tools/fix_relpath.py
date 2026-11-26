# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "annotate_web.py")
t = open(p, encoding="utf-8").read()
old = '        return self._send(200, "saved: " + os.path.relpath(path, ROOT))'
new = '''        try:
            shown = os.path.relpath(path, ROOT)
        except ValueError:  # 跨盘符（项目在 C: junction，数据在 E:）
            shown = os.path.abspath(path)
        return self._send(200, "saved: " + shown)'''
if old in t:
    t = t.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("relpath fixed")
else:
    print("anchor miss")
