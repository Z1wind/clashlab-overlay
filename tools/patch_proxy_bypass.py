# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
line = 'urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))\n'
for name in ("upload_exe20.py", "push_changes.py"):
    p = os.path.join(BASE, "tools", name)
    t = open(p, encoding="utf-8").read()
    if "ProxyHandler({})" in t:
        print(name, "already patched"); continue
    marker = "sys.stdout.reconfigure(encoding=\"utf-8\", errors=\"replace\")\n"
    if marker in t:
        t = t.replace(marker, marker + line, 1)
        open(p, "w", encoding="utf-8", newline="\n").write(t)
        print(name, "proxy bypass added")
    else:
        print(name, "marker miss")
