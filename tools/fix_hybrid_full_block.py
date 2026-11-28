# -*- coding: utf-8 -*-
import os
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
p = os.path.join(BASE, 'tools', 'train_hybrid_full.py')
t = open(p, encoding='utf-8').read()
old = '''    env = os.environ.get("CLASHLAB_EXPORTS", "")
    if env:
        import re as _re
    paths = [x for x in _re.split(r"[;\r\n]+", env) if x.strip()]
    else:'''
new = '''    env = os.environ.get("CLASHLAB_EXPORTS", "")
    if env:
        import re as _re
        paths = [x for x in _re.split(r"[;\r\n]+", env) if x.strip()]
    else:'''
if old in t:
    t = t.replace(old, new, 1)
    open(p, 'w', encoding='utf-8', newline='\n').write(t)
    print('block fixed')
else:
    print('anchor miss')