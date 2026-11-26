# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "overlay", "giant_arrow_diagram.py")
t = open(p, encoding="utf-8").read()
print("has summarize:", "summarize_hits" in t, "| has AIR_TARGETS:", "AIR_TARGETS" in t)

helper = '''AIR_DEFENSE = "air-defense"      # 防空火箭（放空）
AIR_SWEEPER = "air-sweeper"        # 吹风机
AIR_TARGETS = {AIR_DEFENSE, AIR_SWEEPER}
HIDDEN_TYPES = {"hidden-tesla"}    # 默认不现形，不能当已确认目标


def summarize_hits(hits):
    """被穿目标分类：防空火箭 / 吹风机 / 特斯拉(隐身) / 其它。"""
    ad = sum(1 for h in hits if h.get("type") == AIR_DEFENSE)
    sw = sum(1 for h in hits if h.get("type") == AIR_SWEEPER)
    tesla = sum(1 for h in hits if h.get("type") in HIDDEN_TYPES)
    return {"total": len(hits), "air_defense": ad, "air_sweeper": sw,
            "air_total": ad + sw, "tesla_hidden": tesla,
            "other": len(hits) - ad - sw - tesla}


'''
idx = t.find("def match_skewered(")
if idx > 0 and "summarize_hits" not in t:
    t = t[:idx] + helper + t[idx:]
    print("helper inserted at", idx)

def rep(old, new, label):
    global t
    if old in t:
        t = t.replace(old, new, 1)
        print("ok:", label)
    else:
        print("MISS:", label)

rep('''        hits.append({"type": b.get("type") or "", "tile": [int(round(x)), int(round(y))],
                     "t": round(t, 4), "perp": round(perp, 3)})''',
'''        typ = b.get("type") or ""
        hits.append({"type": typ, "tile": [int(round(x)), int(round(y))],
                     "t": round(t, 4), "perp": round(perp, 3),
                     "air": typ in AIR_TARGETS, "hidden": typ in HIDDEN_TYPES})''', "hit tags")

rep('''    for h in hits:
        is_ad = h["type"] == "air-defense"
        col = _pr.THREAT_RED if is_ad else _pr.TEAL''',
'''    for h in hits:
        if h["type"] == AIR_DEFENSE:
            col = _pr.THREAT_RED
        elif h["type"] == AIR_SWEEPER:
            col = _pr.AMBER
        elif h["type"] in HIDDEN_TYPES:
            col = (150, 150, 150)
        else:
            col = _pr.TEAL''', "colors")

rep('''        num = str(h["order"])''', '''        num = "?" if h["type"] in HIDDEN_TYPES else str(h["order"])''', "badge")

rep('''    info = (f"撒兵环 {len(ring_cells)} 格 · 被穿 {len(hits)} 座"
            f"（防空×{sum(1 for h in hits if h['type'] == 'air-defense')}）"''',
'''    _hs = summarize_hits(hits)
    info = (f"撒兵环 {len(ring_cells)} 格 · 被穿 {_hs['total']} 座"
            f"（防空火箭×{_hs['air_defense']} · 吹风机×{_hs['air_sweeper']}"
            f" · 特斯拉隐身×{_hs['tesla_hidden']}）"''', "info")

rep('''    legend = [(_pr.TEAL, "撒兵环=可撒兵格（analysis.deployment_ring）"),
              (_pr.AMBER, "琥珀直线箭头=女王穿云箭 from→to"),
              (_pr.THREAT_RED, "红色编号=被箭线穿到的关键防御"),
              (_pr.AMBER, "底部色条=阶段时序（白框=穿云箭阶段）")]''',
'''    legend = [(_pr.TEAL, "撒兵环=可撒兵格（analysis.deployment_ring）"),
              (_pr.AMBER, "琥珀直线箭头=女王穿云箭 from→to"),
              (_pr.THREAT_RED, "红=防空火箭（放空）；橙=吹风机；灰?=特斯拉（默认不现形）"),
              (_pr.AMBER, "底部色条=阶段时序（白框=穿云箭阶段）")]''', "legend")

rep('''            mark = "◉" if h["type"] == "air-defense" else "○"''',
'''            if h["type"] == AIR_DEFENSE:
                mark = "◉"
            elif h["type"] == AIR_SWEEPER:
                mark = "◍"
            elif h["type"] in HIDDEN_TYPES:
                mark = "?"
            else:
                mark = "○"''', "mark")

open(p, "w", encoding="utf-8", newline="\n").write(t)
print("written", len(t.encode()))
