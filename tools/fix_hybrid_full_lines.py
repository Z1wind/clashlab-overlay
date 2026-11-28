# -*- coding: utf-8 -*-
import os
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
p = os.path.join(BASE, 'tools', 'train_hybrid_full.py')
lines = open(p, encoding='utf-8').read().split('\n')
try:
    i = next(k for k, s in enumerate(lines) if s.startswith('    env = os.environ.get("CLASHLAB_EXPORTS"'))
    j = next(k for k in range(i+1, len(lines)) if lines[k].startswith('    data = []'))
except StopIteration:
    print('markers not found'); raise SystemExit(1)
block = [
    '    env = os.environ.get("CLASHLAB_EXPORTS", "")',
    '    if env:',
    '        import re as _re',
    '        paths = [x for x in _re.split(r"[;\\r\\n]+", env) if x.strip()]',
    '    else:',
    '        paths = [os.path.join(os.path.expanduser("~"), "Downloads", "annot_b01 (1).json"),',
    '                 os.path.join(os.path.expanduser("~"), "Downloads", "annot_b02 (1).json")]',
    '        paths += [os.path.join(os.path.expanduser("~"), "Downloads", "annot_b%02d.json" % i) for i in range(3, 9)]',
]
lines = lines[:i] + block + lines[j:]
open(p, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines))
print('replaced lines', i, '..', j)