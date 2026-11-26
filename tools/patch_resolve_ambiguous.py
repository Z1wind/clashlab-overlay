# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "cocapi.py")
t = open(p, encoding="utf-8").read()

old = '''    if pl:
        res["player"] = pl
        res["match"] = {"by": "player-search"}'''
new = '''    if pl:
        res["player"] = pl
        res["match"] = {"by": "player-search"}
        # 同名玩家很多：OCR 给了部落名时，部落对不上就改用「部落战成员模糊匹配」重新定位
        if clan_name:
            pl_clan = ((pl.get("clan") or {}).get("name") or "")
            if _name_score(clan_name, pl_clan) < 0.5:
                c2, w2, m2 = _find_clan_with_member(name, clan_name, fresh=fresh, ocr_level=ocr_level)
                if m2 and _name_score(name, m2.get("name")) >= 0.85:
                    res["player"] = {"name": m2.get("name"), "tag": m2.get("tag"),
                                     "th": m2.get("th"),
                                     "clan": {"name": (c2 or {}).get("name"),
                                              "tag": (c2 or {}).get("tag")}}
                    res["clan"] = {"name": (c2 or {}).get("name"), "tag": (c2 or {}).get("tag")}
                    res["war"] = w2
                    res["matched_member"] = m2
                    res["match"] = {"by": "war-member-fuzzy"}

    # 候选与歧义标记：同名不同部落时提示，避免「看起来成功其实认错人」
    try:
        cands = search_player(name, limit=5, fresh=fresh) if name else []
        alts = []
        for c in cands:
            alts.append({"name": c.get("name"), "tag": c.get("tag"), "th": c.get("th"),
                         "clan": (c.get("clan") or {}).get("name")})
        res["candidates"] = alts[:5]
        if len({(a.get("clan") or "") for a in alts}) > 1:
            res["ambiguous"] = True
    except Exception:
        res["candidates"] = []'''
if old in t:
    t = t.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("resolve ambiguity patch ok")
else:
    print("anchor miss")
