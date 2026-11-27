# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "cocapi.py")
t = open(p, encoding="utf-8").read()
old = '''def enemy_th_map(clan_tag):
    """当前战争的对手成员 {tag: TH}（无当前战争则用最近一场）。"""
    w = war_members(clan_tag)
    if not w:
        return {}
    return {m["tag"]: m["th"] for m in w["opponent"]["members"] if m.get("tag")}'''
new = '''def enemy_th_map(clan_tag):
    """对手成员 {tag: TH}：优先用公开 cached 档案（实时 TH），其次战争存储数据。"""
    w = war_members(clan_tag)
    if not w:
        return {}
    opp = (w.get("opponent") or {}).get("tag")
    out = {}
    for m in w["opponent"]["members"]:
        if m.get("tag") and isinstance(m.get("th"), int):
            out[m["tag"]] = m["th"]
    if opp:
        try:
            out.update(cached_members_th(opp))
        except Exception:
            pass
    return out'''
if old in t:
    t = t.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("enemy_th_map upgraded")
else:
    print("anchor miss")
