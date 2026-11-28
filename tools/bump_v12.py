# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "desktop_app.py")
t = open(p, encoding="utf-8").read()
t = t.replace('APP_TITLE = "ClashLab 阵型标注（桌面版 v1.1）"', 'APP_TITLE = "ClashLab 阵型标注（桌面版 v1.2）"')
open(p, "w", encoding="utf-8", newline="\n").write(t)
q = os.path.join(BASE, "tools", "build_desktop_v2.py")
s = open(q, encoding="utf-8").read()
s = s.replace("（桌面版 v1.1）", "（桌面版 v1.2）")
open(q, "w", encoding="utf-8", newline="\n").write(s)
print("titles bumped to v1.2")
