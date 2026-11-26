# -*- coding: utf-8 -*-
"""修 OCR 纯数字行；实现 名字/部落 模糊匹配来定位对手。"""
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"

p = os.path.join(BASE, "clashlab", "ocr_screen.py")
t = open(p, encoding="utf-8").read()
t = t.replace('''    name = rest[0] if rest else None
    clan = rest[1] if len(rest) > 1 else None
    return {"level": level, "name": name, "clan": clan}''',
'''    # 纯数字行（等级徽章/胜场数）不当作名字/部落
    rest = [x for x in rest if not re.match(r"^\\d{1,3}$", x)]
    name = rest[0] if rest else None
    clan = rest[1] if len(rest) > 1 else None
    return {"level": level, "name": name, "clan": clan}''')
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("ocr parse fixed")

p2 = os.path.join(BASE, "clashlab", "cocapi.py")
t2 = open(p2, encoding="utf-8").read()
if "def _name_score" not in t2:
    t2 = t2.replace("def resolve_opponent(", '''def _norm_name(s):
    import re as _re
    s = str(s or "").lower()
    s = _re.sub(r"[^0-9a-z\\u4e00-\\u9fff]+", " ", s)
    return " ".join(s.split())


def _name_score(a, b):
    from difflib import SequenceMatcher
    na, nb = _norm_name(a), _norm_name(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    if na in nb or nb in na:
        return 0.9
    return SequenceMatcher(None, na, nb).ratio()


def _search_player_best(name, fresh=True):
    """先精确搜，再用名字前缀/拆分变体兜底；按名字相似度挑最佳。"""
    cands = []
    tried = set()
    variants = [name]
    parts = str(name or "").split()
    if len(parts) > 1:
        variants += [" ".join(parts[:2]), parts[0], parts[-1]]
    if str(name or "").upper() != name:
        variants.append(str(name).upper())
    for q in variants:
        q = (q or "").strip()
        if not q or q.lower() in tried:
            continue
        tried.add(q.lower())
        try:
            cands += search_player(q, limit=5, fresh=fresh)
        except Exception:
            continue
    if not cands:
        return None
    return max(cands, key=lambda c: _name_score(name, c.get("name")))


def _find_clan_with_member(player_name, clan_name=None, fresh=True):
    """按部落名搜候选，再在部落战成员里模糊匹配玩家名，返回 (clan, war, member)。"""
    cands = []
    if clan_name:
        variants = [clan_name, _norm_name(clan_name), str(clan_name).title()]
        for q in variants:
            try:
                cands += search_clan(q, limit=5, fresh=fresh)
            except Exception:
                continue
    best = None
    seen = set()
    for c in cands:
        tag = c.get("tag")
        if not tag or tag in seen:
            continue
        seen.add(tag)
        try:
            war = war_members(tag, fresh=fresh)
        except Exception:
            continue
        if not war:
            continue
        for side in ("clan", "opponent"):
            for m in war[side]["members"]:
                sc = _name_score(player_name, m.get("name"))
                if sc >= 0.6 and (best is None or sc > best[0]):
                    clan_score = _name_score(clan_name, c.get("name")) if clan_name else 0
                    best = (sc + 0.1 * clan_score, c, war, m)
    return best[1:] if best else (None, None, None)


def resolve_opponent(''')
    t2 = t2.replace('''    res = {"query": {"name": name, "clan": clan_name}, "player": None, "clan": None, "war": None}
    if name:
        cands = search_player(name, fresh=fresh)
        if cands:
            res["player"] = cands[0]
    if clan_name:
        cands = search_clan(clan_name, fresh=fresh)
        if cands:
            res["clan"] = cands[0]
    elif res["player"] and res["player"]["clan"].get("tag"):
        res["clan"] = {"name": res["player"]["clan"].get("name"), "tag": res["player"]["clan"].get("tag")}
    if res["clan"] and res["clan"].get("tag"):
        try:
            res["war"] = war_members(res["clan"]["tag"], fresh=fresh)
        except Exception:
            res["war"] = None
    return res''',
'''    import time as _t
    res = {"query": {"name": name, "clan": clan_name}, "player": None, "clan": None,
           "war": None, "matched_member": None, "match": None,
           "fetched_at": _t.strftime("%Y-%m-%dT%H:%M:%S"), "fresh": bool(fresh)}
    # 1) 先按名字找玩家（带兜底变体）
    pl = _search_player_best(name, fresh=fresh) if name else None
    if pl:
        res["player"] = pl
    # 2) 名字没找到，就用部落名找候选部落，再在战争成员里模糊匹配玩家
    if not pl and (name or clan_name):
        clan, war, member = _find_clan_with_member(name, clan_name, fresh=fresh)
        if war:
            res["war"] = war
        if member:
            res["matched_member"] = member
            res["match"] = {"by": "war-member-fuzzy"}
            res["player"] = {"name": member.get("name"), "tag": member.get("tag"),
                             "th": member.get("th"), "clan": {"name": (clan or {}).get("name"),
                                                              "tag": (clan or {}).get("tag")}}
            res["clan"] = {"name": (clan or {}).get("name"), "tag": (clan or {}).get("tag")}
    # 3) 兜底：玩家找到了但没战争数据 -> 用其部落拉战争
    if res["player"] and not res["war"]:
        tag = (res["player"].get("clan") or {}).get("tag")
        if tag:
            try:
                res["war"] = war_members(tag, fresh=fresh)
                res["clan"] = {"name": (res["player"].get("clan") or {}).get("name"), "tag": tag}
            except Exception:
                res["war"] = None
    return res''')
    open(p2, "w", encoding="utf-8", newline="\n").write(t2)
    print("cocapi matcher added")
