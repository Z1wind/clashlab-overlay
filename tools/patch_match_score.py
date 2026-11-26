# -*- coding: utf-8 -*-
"""匹配打分：部落战状态/人数/等级一致性都纳入；并接受 OCR 等级参数。"""
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "cocapi.py")
t = open(p, encoding="utf-8").read()
t = t.replace("def _find_clan_with_member(player_name, clan_name=None, fresh=True):",
              "def _find_clan_with_member(player_name, clan_name=None, fresh=True, ocr_level=None):")
t = t.replace('''    cands = []
    if clan_name:
        variants = [clan_name, _norm_name(clan_name), str(clan_name).title()]
        for q in variants:''',
'''    cands = []
    if clan_name:
        norm = _norm_name(clan_name)
        words = norm.split()
        variants = [clan_name, norm, str(clan_name).title()]
        if len(words) > 1:
            variants += [" ".join(words[:2]), words[0]]
        for q in variants:''')
t = t.replace('''        for side in ("clan", "opponent"):
            for m in war[side]["members"]:
                sc = _name_score(player_name, m.get("name"))
                if sc >= 0.6 and (best is None or sc > best[0]):
                    clan_score = _name_score(clan_name, c.get("name")) if clan_name else 0
                    best = (sc + 0.1 * clan_score, c, war, m)''',
'''        war_bonus = 0.35 if str(war.get("state")) in ("inWar", "preparation") else 0.0
        size_bonus = 0.15 if int(war.get("team_size") or 0) in (15, 20, 25, 30, 40, 50) else 0.0
        for side in ("clan", "opponent"):
            for m in war[side]["members"]:
                name_sc = _name_score(player_name, m.get("name"))
                if name_sc < 0.6:
                    continue
                clan_sc = _name_score(clan_name, c.get("name")) if clan_name else 0.0
                lv_bonus = 0.0
                if ocr_level and m.get("th"):
                    try:
                        diff = abs(int(m["th"]) - int(str(ocr_level).rstrip(".．、本")))
                        lv_bonus = 0.25 if diff <= 1 else (-0.4 if diff >= 3 else 0.0)
                    except Exception:
                        lv_bonus = 0.0
                sc = name_sc + 0.4 * clan_sc + war_bonus + size_bonus + lv_bonus
                if best is None or sc > best[0]:
                    best = (sc, c, war, m)''')
t = t.replace("def resolve_opponent(name=None, clan_name=None, fresh=True):",
              "def resolve_opponent(name=None, clan_name=None, fresh=True, ocr_level=None):")
t = t.replace("        clan, war, member = _find_clan_with_member(name, clan_name, fresh=fresh)",
              "        clan, war, member = _find_clan_with_member(name, clan_name, fresh=fresh, ocr_level=ocr_level)")
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("matcher scoring patched")

# CLI 传 ocr level
p2 = os.path.join(BASE, "tools", "ocr_opponent.py")
t2 = open(p2, encoding="utf-8").read()
t2 = t2.replace("res = cocapi.resolve_opponent(got[\"name\"], got[\"clan\"], fresh=True)",
                "res = cocapi.resolve_opponent(got[\"name\"], got[\"clan\"], fresh=True, ocr_level=got.get(\"level\"))")
open(p2, "w", encoding="utf-8", newline="\n").write(t2)
print("cli patched")
