# -*- coding: utf-8 -*-
import os, re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "build_desktop_html.py")
t = open(p, encoding="utf-8").read()
if "re.sub(r'<title>" not in t:
    t = t.replace('t = t.replace("<title>ClashLab 阵型标注（HTML 版）</title>", "<title>ClashLab 阵型标注（桌面版）</title>")',
                  't = re.sub(r"<title>.*?</title>", "<title>ClashLab 阵型标注（桌面版）</title>", t, count=1)')
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("title patch updated")
else:
    print("already patched")
