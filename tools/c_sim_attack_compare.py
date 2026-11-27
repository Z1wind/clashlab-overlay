# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "tools", "sim_attack.py")
t = open(p, encoding="utf-8").read()
if "--compare" not in t:
    t = t.replace('    ap.add_argument("--json", action="store_true")',
                  '    ap.add_argument("--compare", action="store_true", help="对比 3 种配比")\n    ap.add_argument("--json", action="store_true")')
    t = t.replace('''    lay = json.load(open(a.layout, encoding="utf-8"))
    army, spells = load_army({"army": a.army, "troops": a.troops, "th": a.th})''',
'''    lay = json.load(open(a.layout, encoding="utf-8"))
    if a.compare:
        from clashlab import battle_sim
        PRESETS = {
            "ground": ({"root-rider": 6, "golem": 3, "witch": 6, "healer": 4},
                       {"rage": 2, "heal": 2, "freeze": 1, "jump": 1}, ["queen", "king", "warden"]),
            "air": ({"edrag": 8, "balloon": 12, "healer": 4},
                    {"rage": 2, "freeze": 2, "haste": 1}, ["queen", "warden"]),
            "hybrid": ({"miner": 21, "hog-rider": 11, "healer": 4},
                       {"heal": 3, "rage": 2}, ["queen", "king"]),
        }
        rows = []
        for name, (army, spells, heroes) in PRESETS.items():
            r = battle_sim.simulate(lay, army, spells=spells, th=a.th, heroes=heroes)
            rows.append((name, army, spells, heroes, r))
        if a.json:
            print(json.dumps([{"comp": n, "result": r} for n, _a, _s, _h, r in rows], ensure_ascii=False, indent=1))
            return 0
        print("# 配比对比（启发式）:", lay.get("name") or a.layout)
        print("%-8s %-7s %-8s %-8s %-8s %-6s" % ("配比", "星级", "生存%", "拆本s", "兵力DPS", "破墙"))
        for name, army, spells, heroes, r in rows:
            if not r.get("ok"):
                print("%-8s 失败: %s" % (name, r.get("error"))); continue
            print("%-8s %-7s %-8.0f %-8s %-8s %-6s" % (
                name, r["stars_estimate"], r["survival"] * 100, r["th_ttk_s"], r["army_dps"], r["walls_to_break"]))
        return 0
    army, spells = load_army({"army": a.army, "troops": a.troops, "th": a.th})''')
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("sim_attack compare added")
