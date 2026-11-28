# -*- coding: utf-8 -*-
import os
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
p = os.path.join(BASE, 'tools', 'eval_hybrid_variants.py')
t = open(p, encoding='utf-8').read()
t = t.replace('crop(img, cal, cx+.5, cy+.5, shift=sh)', 'crop(img, cal, cx, cy, shift=sh)')
t = t.replace('crop(img, cal, cx+.5, cy+.5)', 'crop(img, cal, cx, cy)')
open(p, 'w', encoding='utf-8', newline='\n').write(t)
print('eval crop center fixed; remaining cx+.5:', t.count('cx+.5, cy+.5'))