# -*- coding: utf-8 -*-
import os
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
p = os.path.join(BASE, 'clashlab', 'wargame.py')
t = open(p, encoding='utf-8').read()
old = '''def _norm_spawn_list(spawn):
    """把 spawn 归一成点列表：支持单点 (x,y) 或线/区域 [(x,y),(x,y)...]。"""
    if isinstance(spawn, (list, tuple)) and len(spawn) >= 2 and all(
            isinstance(p, (list, tuple)) and len(p) == 2 for p in spawn):
        return [(int(round(p[0])), int(round(p[1]))) for p in spawn]
    return [(int(round(spawn[0])), int(round(spawn[1])))]'''
new = '''def _norm_spawn_list(spawn):
    """把 spawn 归一成点列表：支持单点 (x,y) 或线/区域 [(x,y),(x,y)...]。"""
    if (isinstance(spawn, (list, tuple)) and len(spawn) >= 1
            and all(isinstance(p, (list, tuple)) and len(p) == 2 for p in spawn)):
        return [(int(round(float(p[0]))), int(round(float(p[1])))) for p in spawn]
    return [(int(round(float(spawn[0]))), int(round(float(spawn[1]))))]'''
if old in t:
    t = t.replace(old, new)
    open(p, 'w', encoding='utf-8', newline=chr(10)).write(t)
    print('spawn normalizer patched')
else:
    print('anchor miss')
