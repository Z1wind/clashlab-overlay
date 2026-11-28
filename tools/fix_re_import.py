# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "build_desktop_html.py")
t = open(p, encoding="utf-8").read()
if "import re" not in t.split("\n")[1] and "\nimport re" not in t:
    t = t.replace("import base64, os, sys", "import base64, os, re, sys", 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("import re added")
else:
    print("re ok")
