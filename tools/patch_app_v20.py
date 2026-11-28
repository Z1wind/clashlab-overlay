# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "desktop_app.py")
t = open(p, encoding="utf-8").read()
t = t.replace('APP_TITLE = "ClashLab 阵型标注（桌面版 v1.6）"', 'APP_TITLE = "ClashLab 阵型标注（桌面版 v2.0）"')
t = t.replace('html = resource_path("ClashLabAnnotator_Desktop_v4.html")', 'html = resource_path("ClashLabAnnotator_Desktop_v5.html")')
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("app v2.0 html v5")
