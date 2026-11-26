# -*- coding: utf-8 -*-
import os
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
p = os.path.join(BASE, 'clashlab', 'strategy.py')
t = open(p, encoding='utf-8').read()
old = '        out.append({"title": query, "url": YT + urllib.parse.quote_plus(query)})'
new = '        out.append({"title": "YouTube 搜索：" + query, "url": YT + urllib.parse.quote_plus(query)})'
if old in t:
    t = t.replace(old, new)
    open(p, 'w', encoding='utf-8', newline=chr(10)).write(t)
    print('title patched')
else:
    print('anchor miss')
