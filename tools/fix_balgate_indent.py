# -*- coding: utf-8 -*-
import os
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
p = os.path.join(BASE, 'tools', 'train_hybrid_balgate_cv.py')
lines = open(p, encoding='utf-8').read().split('\n')
new_block = [
    '                _cnt = {}',
    '                for _t in gpos_types: _cnt[_t] = _cnt.get(_t, 0) + 1',
    '                _w = [1.0 / (_cnt[_t] ** 0.5) for _t in gpos_types]',
    '                _pick = rng.choices(gpos, weights=_w, k=40)',
    '                items = [(aug(c,rng),l) for (c,l) in _pick + [gneg[rng.randrange(len(gneg))] for _ in range(40)]]',
]
lines[73:78] = new_block
open(p, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines))
print('indent fixed')