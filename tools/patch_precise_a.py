# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "desktop_app.py")
t = open(p, encoding="utf-8").read()
t = t.replace('"precise": (0.90, 0.85, (0.0, 0.5)),  # 少错：半格合并，精度 +7pt（CV）',
              '"precise": (0.90, 0.90, (0.0, 0.5)),  # 少错：半格合并 + 高阈值（b03: P92.5/R81.3/type98.6）')
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("precise cfg updated")
