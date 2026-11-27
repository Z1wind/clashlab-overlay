# -*- coding: utf-8 -*-
import os, re
BASE = r"C:\Users\Admin（无密码）\\Doubao\\chats\\2026-11-23\\new-chat".replace("\\\\", "\\")
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
# 1) self_check 接入战斗模拟
p = os.path.join(BASE, "tools", "self_check.py")
t = open(p, encoding="utf-8").read()
if "battle_sim" not in t:
    anchor = '    if isinstance(recs, dict) and recs.get("error"):'
    add = '''    # 进攻模拟（启发式，用推荐打法里的兵种）
    try:
        from clashlab import battle_sim
        army = {}
        first = None
        if isinstance(recs, dict):
            _rs = recs.get("recommendations") or recs.get("items") or []
            first = _rs[0] if _rs else None
        elif isinstance(recs, list) and recs:
            first = recs[0]
        if first:
            army = first.get("troops") or {}
        if army:
            sim = battle_sim.simulate(lay, army)
            print("\\n## 进攻模拟（启发式）")
            if sim.get("ok"):
                print("- 推荐侧 %s｜路径 %s 格｜破墙 %s｜暴露 DPS %s｜生存率 %.0f%%｜拆本 %ss｜预估星级 %s" % (
                    sim["side"], sim["path_len"], sim["walls_to_break"], sim["exposure_dps"],
                    sim["survival"] * 100, sim["th_ttk_s"], sim["stars_estimate"]))
            else:
                print("- 无法模拟:", sim.get("error"))
    except Exception as e:
        print("\\n## 进攻模拟：失败（%s）" % str(e)[:100])
'''
    if anchor in t:
        t = t.replace(anchor, add + anchor, 1)
        open(p, "w", encoding="utf-8", newline="\n").write(t)
        print("self_check + sim")
    else:
        print("self_check anchor miss")
# 2) 版本 0.3.3
p2 = os.path.join(BASE, "clashlab", "__init__.py")
t2 = open(p2, encoding="utf-8").read()
t2 = re.sub(r'__version__ = "[^"]+"', '__version__ = "0.3.3"', t2)
open(p2, "w", encoding="utf-8", newline="\n").write(t2)
print("version 0.3.3")
