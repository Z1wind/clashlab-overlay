# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "build_apk_ci.py")
t = open(p, encoding="utf-8").read()
t = t.replace('        print(p.stdout[-2000:]); print(p.stderr[-3000:])',
              '        print((p.stdout or "")[-2000:]); print((p.stderr or "")[-3000:])')
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("guard patched")
