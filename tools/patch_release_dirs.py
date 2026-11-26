# -*- coding: utf-8 -*-
import os
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
p = os.path.join(BASE, 'tools', 'make_release.py')
t = open(p, encoding='utf-8').read()
old = 'INCLUDE_DIRS = ["clashlab", "tests", "bases", "assets", "config", "docs", "layouts"]'
new = 'INCLUDE_DIRS = ["clashlab", "tests", "bases", "assets", "config", "docs", "layouts", "knowledge", "models"]'
if old in t:
    t = t.replace(old, new)
    open(p, 'w', encoding='utf-8', newline=chr(10)).write(t)
    print('release includes updated')
else:
    print('anchor miss')
