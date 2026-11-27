# -*- coding: utf-8 -*-
import os, re
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "__init__.py")
t = open(p, encoding="utf-8").read()
t = re.sub(r'__version__ = "[^"]+"', '__version__ = "0.3.2"', t)
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("version 0.3.2")
