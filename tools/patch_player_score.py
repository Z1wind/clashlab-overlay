# -*- coding: utf-8 -*-
"""玩家候选打分：名字 + 部落名 + OCR 等级一致性。"""
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "cocapi.py")
t = open(p, encoding="utf-8").read()
t = t.replace("def _search_player_best(name, fresh=True):",
              "def _search_player_best(name, clan_name=None, ocr_level=None, fresh=True):")
t = t.replace('''    if not cands:
        return None
    return max(cands, key=lambda c: _name_score(name, c.get("name")))''',
'''    if not cands:
        return None
    def score(c):
        s = _name_score(name, c.get("name"))
        if clan_name:
            s += 0.5 * _name_score(clan_name, ((c.get("clan") or {}).get("name") or ""))
        if ocr_level and c.get("th"):
            try:
                diff = abs(int(c["th"]) - int(str(ocr_level).rstrip(".．、本")))
                s += 0.4 if diff <= 1 else (-0.5 if diff >= 3 else 0.0)
            except Exception:
                pass
        return s
    return max(cands, key=score)''')
t = t.replace("    pl = _search_player_best(name, fresh=fresh) if name else None",
              "    pl = _search_player_best(name, clan_name=clan_name, ocr_level=ocr_level, fresh=fresh) if name else None")
t = t.replace('''    if pl:
        res["player"] = pl''',
'''    if pl:
        res["player"] = pl
        res["match"] = {"by": "player-search"}''')
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("player scoring patched")
