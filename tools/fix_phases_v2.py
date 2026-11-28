# -*- coding: utf-8 -*-
import os
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
p = os.path.join(BASE, 'tools', 'preannotate_core.py')
lines = open(p, encoding='utf-8').read().split('\n')
# 修复 PreAnnotator（第一处）：把 phases 用法还原
for i, s in enumerate(lines):
    if s.strip() == 'cells = [(cx + off, cy + off) for off in phases for cx in range(2, 42) for cy in range(2, 42)]' and i < 60:
        lines[i] = '        cells = [(cx, cy) for cx in range(2, 42) for cy in range(2, 42)]'
        print('restored PreAnnotator cells at line', i+1)
# HybridAnnotator：加 phases 参数并使用
for i, s in enumerate(lines):
    if s.strip() == 'def detect(self, img, quad, gate_th=None, emb_th=None):':
        lines[i] = '    def detect(self, img, quad, gate_th=None, emb_th=None, phases=(0.0,)):'
        print('patched Hybrid detect signature at line', i+1)
        for j in range(i, min(i+12, len(lines))):
            if lines[j].strip() == 'cells = [(cx, cy) for cx in range(2, 42) for cy in range(2, 42)]':
                lines[j] = '        cells = [(cx + off, cy + off) for off in phases for cx in range(2, 42) for cy in range(2, 42)]'
                print('patched Hybrid cells at line', j+1)
                break
        break
open(p, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines))