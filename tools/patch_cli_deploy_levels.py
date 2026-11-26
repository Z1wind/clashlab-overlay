# -*- coding: utf-8 -*-
"""wargame_cli / deploy 透传等级参数。"""
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"

# CLI
p = os.path.join(BASE, "tools", "wargame_cli.py")
t = open(p, encoding="utf-8").read()
miss = []
def rep(s, old, new, label):
    if old not in s:
        miss.append(label); return s
    return s.replace(old, new, 1)
if "--troop-levels" not in t:
    t = rep(t, '    ap.add_argument("--workers", type=int, default=None)',
              '    ap.add_argument("--workers", type=int, default=None)\n'
              '    ap.add_argument("--troop-levels", default=None, help="例如 giant=10,wizard=9")\n'
              '    ap.add_argument("--hero-levels", default=None, help="例如 queen=80,king=75")\n'
              '    ap.add_argument("--building-levels", default=None, help="覆盖布局里所有建筑等级，例如 8")',
              "cli args")
    t = rep(t, "def _parse_army(", "def _parse_army(", "noop")
    # parse helper + pass into run
    if "_parse_level_map" not in t:
        t = t.replace("def main(", '''def _parse_level_map(text):
    out = {}
    for part in str(text or "").split(","):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            raise ValueError("等级格式应为 key=level：%r" % part)
        k, v = part.split("=", 1)
        out[k.strip()] = int(v)
    return out


def main(''', 1)
    t = rep(t, "    res = wargame.run(", "    res = wargame.run(", "noop2")
    # 找到 run( 调用并注入参数：在 res = wargame.run(...) 的收尾括号前加参数
    import re
    m = re.search(r"(res = wargame\.run\((?:.|\n)*?)\)\n", t)
    if m:
        block = m.group(1)
        if "troop_levels=" not in block:
            t = t[:m.start()] + block + (",\n                       troop_levels=_parse_level_map(a.troop_levels) if a.troop_levels else None,\n"
                                        "                       hero_levels=_parse_level_map(a.hero_levels) if a.hero_levels else None") + t[m.end():]
    open(p, "w", encoding="utf-8", newline=chr(10)).write(t)
    print("cli patched; miss:", miss)
else:
    print("cli already patched")

# deploy: evaluate/optimize 透传
p2 = os.path.join(BASE, "clashlab", "deploy.py")
t2 = open(p2, encoding="utf-8").read()
if "troop_levels" not in t2:
    t2 = t2.replace("def evaluate(layout, army, cand, trials=10, seed=1, tick=wargame.DEFAULT_TICK, max_time=wargame.DEFAULT_MAX_TIME):",
                    "def evaluate(layout, army, cand, trials=10, seed=1, tick=wargame.DEFAULT_TICK, max_time=wargame.DEFAULT_MAX_TIME,\n             troop_levels=None, hero_levels=None):")
    t2 = t2.replace("""        r = wargame.simulate_once(layout, army, spawn=cand["points"],
                                  seed=int(seed) * 100000 + k, tick=tick,
                                  max_time=max_time, collect_events=False)""",
"""        r = wargame.simulate_once(layout, army, spawn=cand["points"],
                                  seed=int(seed) * 100000 + k, tick=tick,
                                  max_time=max_time, troop_levels=troop_levels,
                                  hero_levels=hero_levels, collect_events=False)""")
    t2 = t2.replace("def optimize(layout, army, mode=\"line\", trials=10, seed=1):",
                    "def optimize(layout, army, mode=\"line\", trials=10, seed=1, troop_levels=None, hero_levels=None):")
    t2 = t2.replace("    rows = [evaluate(layout, army, c, trials=trials, seed=seed) for c in cands]",
                    "    rows = [evaluate(layout, army, c, trials=trials, seed=seed,\n                     troop_levels=troop_levels, hero_levels=hero_levels) for c in cands]")
    t2 = t2.replace('        base = evaluate(layout, army, point_candidates(layout)[0], trials=trials, seed=seed)',
                    '        base = evaluate(layout, army, point_candidates(layout)[0], trials=trials, seed=seed,\n                        troop_levels=troop_levels, hero_levels=hero_levels)')
    open(p2, "w", encoding="utf-8", newline=chr(10)).write(t2)
    print("deploy patched")
else:
    print("deploy already patched")
