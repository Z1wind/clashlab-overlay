# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "cocapi.py")
t = open(p, encoding="utf-8").read()
old = '''def player_th(tag):
    """从最近攻防记录推断玩家 TH（防御记录里的 defenderTownhall 最可靠）。"""
    items = player_war_attacks(tag)
    mine = str(tag).strip().lstrip("#").upper()
    counts = {}
    for it in items:
        dt = str(it.get("defenderTag") or "").lstrip("#").upper()
        at = str(it.get("attackerTag") or "").lstrip("#").upper()
        if dt == mine and it.get("defenderTownhall"):
            counts[int(it["defenderTownhall"])] = counts.get(int(it["defenderTownhall"]), 0) + 1
        elif at == mine and it.get("attackerTownhall"):
            counts[int(it["attackerTownhall"])] = counts.get(int(it["attackerTownhall"]), 0) + 1
    if not counts:
        return None
    return max(counts.items(), key=lambda kv: kv[1])[0]'''
new = '''def player_th(tag):
    """推断玩家当前 TH：优先「最近一场战争」里的记录（玩家会升 TH，历史记录不可靠）。"""
    items = player_war_attacks(tag)
    mine = str(tag).strip().lstrip("#").upper()

    def ts(it):
        return str(it.get("warEndTime") or "")

    latest = None
    for it in sorted(items, key=ts, reverse=True):
        dt = str(it.get("defenderTag") or "").lstrip("#").upper()
        at = str(it.get("attackerTag") or "").lstrip("#").upper()
        if dt == mine and it.get("defenderTownhall"):
            latest = int(it["defenderTownhall"]); break
        if at == mine and it.get("attackerTownhall"):
            latest = int(it["attackerTownhall"]); break
    if latest:
        return latest
    counts = {}
    for it in items:
        dt = str(it.get("defenderTag") or "").lstrip("#").upper()
        at = str(it.get("attackerTag") or "").lstrip("#").upper()
        if dt == mine and it.get("defenderTownhall"):
            counts[int(it["defenderTownhall"])] = counts.get(int(it["defenderTownhall"]), 0) + 1
        elif at == mine and it.get("attackerTownhall"):
            counts[int(it["attackerTownhall"])] = counts.get(int(it["attackerTownhall"]), 0) + 1
    if not counts:
        return None
    return max(counts.items(), key=lambda kv: kv[1])[0]'''
if old in t:
    t = t.replace(old, new)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("player_th latest-first patched")
else:
    print("anchor miss")
