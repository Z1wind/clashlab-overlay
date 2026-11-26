# -*- coding: utf-8 -*-
"""wargame 等级支持补丁：建筑 level、troop_levels、hero_levels。"""
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "wargame.py")
t = open(p, encoding="utf-8").read()
orig = t
miss = []

def rep(old, new, count=1, label=""):
    global t
    if old not in t:
        miss.append(label or old[:40])
        return
    t = t.replace(old, new, count)

# 1) 插入 _guess_th 与等级缩放辅助
rep('''def parse_layout(data):''',
'''def _guess_th(text):
    import re as _re
    m = _re.search(r"th(\\d{1,2})", str(text or ""), _re.I)
    return int(m.group(1)) if m else 16


def parse_layout(data):''')

# 2) parse_layout 中按 level 缩放
rep('''        rng = float(raw["range"]) if raw.get("range") is not None else float(st["range"])''',
'''        rng = float(raw["range"]) if raw.get("range") is not None else float(st["range"])
        lvl = raw.get("level")
        if lvl is not None and raw.get("hp") is None:
            from . import levels as _levels
            _mx = _levels.max_level_of(typ, _guess_th(name))
            _sc = _levels.building_scale(lvl, _mx)
            hp *= float(_sc["hp"])
            dps *= float(_sc["dps"])''')

# 3) building dict 带 level
rep('''            "source": raw.get("source"),
        })''',
'''            "source": raw.get("source"),
            "level": (int(lvl) if lvl is not None else None),
        })''')

# 4) _expand_units 支持等级
rep('def _expand_units(army, space, spawn, rng, grid):',
    'def _expand_units(army, space, spawn, rng, grid, troop_levels=None, hero_levels=None):')
rep('''    prefer = np.zeros(U, dtype=bool)
    for i, name in enumerate(names):''',
'''    prefer = np.zeros(U, dtype=bool)
    hero_boost = 1.0
    if hero_levels:
        from . import levels as _levels
        hero_boost = float(_levels.army_boost(hero_levels))
    for i, name in enumerate(names):''')
rep('''        hp[i] = float(st["hp"])
        dps[i] = float(st["dps"])''',
'''        hp_i, dps_i = float(st["hp"]), float(st["dps"])
        if troop_levels:
            _lv = dict(troop_levels).get(name)
            if _lv is not None:
                from . import levels as _levels
                _sc = _levels.troop_scale(_lv)
                hp_i *= float(_sc["hp"])
                dps_i *= float(_sc["dps"])
        hp[i] = hp_i
        dps[i] = dps_i * hero_boost''')

# 5) multi 透传
rep('def _expand_units_multi(army, spawns, space, rng, grid):',
    'def _expand_units_multi(army, spawns, space, rng, grid, troop_levels=None, hero_levels=None):')
rep('            parts.append(_expand_units(sub, space, sp, rng, grid))',
    '            parts.append(_expand_units(sub, space, sp, rng, grid,\n                                       troop_levels=troop_levels, hero_levels=hero_levels))')
rep('        return _expand_units(army, space, spawns[0], rng, grid)',
    '        return _expand_units(army, space, spawns[0], rng, grid,\n                             troop_levels=troop_levels, hero_levels=hero_levels)')

# 6) simulate_once 签名与调用
rep('''def simulate_once(layout, army, *, spawn=(2, 2), seed=0, tick=DEFAULT_TICK,
                  max_time=DEFAULT_MAX_TIME, wall_hp=DEFAULT_WALL_HP,
                  collect_events=True):''',
'''def simulate_once(layout, army, *, spawn=(2, 2), seed=0, tick=DEFAULT_TICK,
                  max_time=DEFAULT_MAX_TIME, wall_hp=DEFAULT_WALL_HP,
                  troop_levels=None, hero_levels=None,
                  collect_events=True):''')
rep('''    names, u_pos, u_hp, u_dps, u_speed, u_range, u_prefer = _expand_units_multi(
        army_p, spawns, L.passable, rng, grid)''',
'''    names, u_pos, u_hp, u_dps, u_speed, u_range, u_prefer = _expand_units_multi(
        army_p, spawns, L.passable, rng, grid,
        troop_levels=troop_levels, hero_levels=hero_levels)''')

# 7) 多进程 worker / trials / run 透传
rep('''    layout, army, tasks, tick, max_time, wall_hp = payload''',
'''    layout, army, tasks, tick, max_time, wall_hp, troop_levels, hero_levels = payload''')
rep('''        r = simulate_once(layout, army, spawn=spawn, seed=seed_pair, tick=tick,
                          max_time=max_time, wall_hp=wall_hp, collect_events=False)''',
'''        r = simulate_once(layout, army, spawn=spawn, seed=seed_pair, tick=tick,
                          max_time=max_time, wall_hp=wall_hp,
                          troop_levels=troop_levels, hero_levels=hero_levels,
                          collect_events=False)''')
rep('def _run_trials(L, army_p, tasks, tick, max_time, wall_hp, workers=1):',
    'def _run_trials(L, army_p, tasks, tick, max_time, wall_hp, workers=1,\n                troop_levels=None, hero_levels=None):')
rep('''            payloads = [(L, army_p, tasks[bounds[k]:bounds[k + 1]], tick, max_time, wall_hp)
                        for k in range(n) if bounds[k] < bounds[k + 1]]''',
'''            payloads = [(L, army_p, tasks[bounds[k]:bounds[k + 1]], tick, max_time, wall_hp,
                         troop_levels, hero_levels)
                        for k in range(n) if bounds[k] < bounds[k + 1]]''')
rep('''        r = simulate_once(L, army_p, spawn=spawn, seed=seed_pair, tick=tick,
                          max_time=max_time, wall_hp=wall_hp, collect_events=False)''',
'''        r = simulate_once(L, army_p, spawn=spawn, seed=seed_pair, tick=tick,
                          max_time=max_time, wall_hp=wall_hp,
                          troop_levels=troop_levels, hero_levels=hero_levels,
                          collect_events=False)''')
rep('''def run(layout, army, trials=DEFAULT_TRIALS, seed=1, tick=DEFAULT_TICK,
        max_time=DEFAULT_MAX_TIME, wall_hp=DEFAULT_WALL_HP, workers=1):''',
'''def run(layout, army, trials=DEFAULT_TRIALS, seed=1, tick=DEFAULT_TICK,
        max_time=DEFAULT_MAX_TIME, wall_hp=DEFAULT_WALL_HP, workers=1,
        troop_levels=None, hero_levels=None):''')
rep('    rows = _run_trials(L, army_p, tasks, tick, max_time, wall_hp, workers=workers)',
    '    rows = _run_trials(L, army_p, tasks, tick, max_time, wall_hp, workers=workers,\n                       troop_levels=troop_levels, hero_levels=hero_levels)')
rep('''    best_run = simulate_once(L, army_p, spawn=best_spawn, seed=(int(seed), best_trial),
                             tick=tick, max_time=max_time, wall_hp=wall_hp,
                             collect_events=True)''',
'''    best_run = simulate_once(L, army_p, spawn=best_spawn, seed=(int(seed), best_trial),
                             tick=tick, max_time=max_time, wall_hp=wall_hp,
                             troop_levels=troop_levels, hero_levels=hero_levels,
                             collect_events=True)''')

if t != orig:
    open(p, "w", encoding="utf-8", newline=chr(10)).write(t)
    print("wargame patched, missing:", miss)
else:
    print("no change; missing:", miss)
