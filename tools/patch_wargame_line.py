# -*- coding: utf-8 -*-
import os
BASE = r'C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat'
p = os.path.join(BASE, 'clashlab', 'wargame.py')
t = open(p, encoding='utf-8').read()

helper = '''
def _norm_spawn_list(spawn):
    """把 spawn 归一成点列表：支持单点 (x,y) 或线/区域 [(x,y),(x,y)...]。"""
    if isinstance(spawn, (list, tuple)) and len(spawn) >= 2 and all(
            isinstance(p, (list, tuple)) and len(p) == 2 for p in spawn):
        return [(int(round(p[0])), int(round(p[1]))) for p in spawn]
    return [(int(round(spawn[0])), int(round(spawn[1])))]


def _expand_units_multi(army, spawns, space, rng, grid):
    """按 spawn 数量拆分军队后逐个展开，返回拼接后的数组（线/区域投放）。"""
    n = max(1, len(spawns))
    parts = []
    for si, sp in enumerate(spawns):
        sub = {}
        for name, count in army.items():
            c = int(count)
            base_c = c // n + (1 if si < (c % n) else 0)
            if base_c > 0:
                sub[name] = base_c
        if sub:
            parts.append(_expand_units(sub, space, sp, rng, grid))
    if not parts:
        return _expand_units(army, space, spawns[0], rng, grid)
    names = []
    for part in parts:
        names.extend(part[0])
    return (names,) + tuple(np.concatenate([part[k] for part in parts]) for k in range(1, 7))


'''
anchor = 'def simulate_once('
if '_norm_spawn_list' in t:
    print('already patched')
else:
    t = t.replace(anchor, helper + anchor, 1)
    old_expand = '''    names, u_pos, u_hp, u_dps, u_speed, u_range, u_prefer = _expand_units(
        army_p, L.passable, spawn, rng, grid)'''
    new_expand = '''    spawns = _norm_spawn_list(spawn)
    names, u_pos, u_hp, u_dps, u_speed, u_range, u_prefer = _expand_units_multi(
        army_p, spawns, L.passable, rng, grid)'''
    if old_expand in t:
        t = t.replace(old_expand, new_expand, 1)
    else:
        print('expand anchor miss')
    old_ev = '''            "detail": "spawn=(%d,%d) units=%d" % (int(spawn[0]), int(spawn[1]), U),'''
    new_ev = '''            "detail": ("spawn=(%d,%d) units=%d" % (int(spawns[0][0]), int(spawns[0][1]), U)
                       if len(spawns) == 1 else
                       "spawn_line=[%s] units=%d" % (",".join("%d,%d" % s for s in spawns), U)),'''
    if old_ev in t:
        t = t.replace(old_ev, new_ev, 1)
    else:
        print('event anchor miss')
    open(p, 'w', encoding='utf-8', newline=chr(10)).write(t)
    print('wargame patched, bytes', len(t.encode()))
