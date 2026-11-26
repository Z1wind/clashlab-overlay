# -*- coding: utf-8 -*-
import os
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
# strategy.py: add YOUTUBE_SEARCH alias
p = os.path.join(BASE, 'clashlab', 'strategy.py')
t = open(p, encoding='utf-8').read()
if 'YOUTUBE_SEARCH' not in t:
    t = t.replace('YT = "https://www.youtube.com/results?search_query="',
                  'YT = YOUTUBE_SEARCH = "https://www.youtube.com/results?search_query="')
    open(p, 'w', encoding='utf-8', newline=chr(10)).write(t)
    print('alias added')
else:
    print('alias exists')
# cli: force utf-8 stdout
p2 = os.path.join(BASE, 'tools', 'strategy_cli.py')
t2 = open(p2, encoding='utf-8').read()
if 'reconfigure' not in t2:
    t2 = t2.replace('ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))',
                    'try:' + chr(10) + '    sys.stdout.reconfigure(encoding="utf-8")' + chr(10) +
                    'except Exception:' + chr(10) + '    pass' + chr(10) + chr(10) +
                    'ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))', 1)
    open(p2, 'w', encoding='utf-8', newline=chr(10)).write(t2)
    print('cli utf8 patched')
else:
    print('cli already patched')
