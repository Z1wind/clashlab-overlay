# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
# desktop_app: 优先加载 v2 html
p = os.path.join(BASE, "tools", "desktop_app.py")
t = open(p, encoding="utf-8").read()
if "ClashLabAnnotator_Desktop_v2.html" not in t:
    t = t.replace('html = resource_path("ClashLabAnnotator_HTML_desktop.html")',
                  'html = resource_path("ClashLabAnnotator_Desktop_v2.html")', 1)
    t = t.replace('APP_TITLE = "ClashLab 阵型标注（桌面版）"', 'APP_TITLE = "ClashLab 阵型标注（桌面版 v1.1）"', 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("desktop_app updated")
else:
    print("already")
# build script: 指向 v2 html
q = os.path.join(BASE, "tools", "build_exe3.ps1")
s = open(q, encoding="utf-8").read()
s = s.replace("ClashLabAnnotator_HTML_desktop.html", "ClashLabAnnotator_Desktop_v2.html")
open(q, "w", encoding="utf-8", newline="\n").write(s)
print("build script updated")
