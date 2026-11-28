# -*- coding: utf-8 -*-
import os
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
p = os.path.join(BASE, 'tools', 'preannotate_core.py')
lines = open(p, encoding='utf-8').read().split('\n')
done = False
for i, s in enumerate(lines):
    if s.strip() == 'def detect(self, img, quad, gate_th=None, emb_th=None, phases=(0.0,)):':
        for j in range(i, min(i+15, len(lines))):
            if lines[j].strip() == 'cells = [(cx, cy) for cx in range(2, 42) for cy in range(2, 42)]':
                lines[j] = '        cells = [(cx + off, cy + off) for off in phases for cx in range(2, 42) for cy in range(2, 42)]'
                print('patched Hybrid cells at line', j+1); done = True; break
        break
if not done: print('not found')
open(p, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines))