# -*- coding: utf-8 -*-
import os
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
p = os.path.join(BASE, 'tools', 'train_hybrid_full.py')
lines = open(p, encoding='utf-8').read().split('\n')
# 保留到 ONNX 段之前；ONNX 导出改由 export_hybrid_onnx.py 负责（避免 CPU/GPU dummy 冲突）
cut = next((k for k, s in enumerate(lines) if s.strip() == '# ONNX'), None)
if cut is None:
    print('no ONNX marker')
else:
    lines = lines[:cut]
    lines.append("print('saved pt/npz/meta; run tools/export_hybrid_onnx.py for ONNX', flush=True)")
    lines.append('')
    open(p, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines))
    print('ONNX block removed at line', cut)