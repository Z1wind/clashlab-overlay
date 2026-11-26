# -*- coding: utf-8 -*-
import os
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
p = os.path.join(BASE, 'clashlab', 'deploy.py')
t = open(p, encoding='utf-8').read()
old = '''def _g(layout):
    lay = layout if isinstance(layout, dict) else wargame.load_layout(layout)
    try:
        return int(lay.grid)
    except Exception:
        return 44'''
new = '''def _g(layout):
    if isinstance(layout, dict):
        return int(layout.get("grid") or 44)
    try:
        return int(wargame.load_layout(layout).grid)
    except Exception:
        return 44'''
if old in t:
    t = t.replace(old, new)
    open(p, 'w', encoding='utf-8', newline=chr(10)).write(t)
    print('patched _g')
else:
    print('anchor miss')
