# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "cocapi.py")
t = open(p, encoding="utf-8").read()
if "def search_player" not in t:
    add = '''

def search_player(name, limit=5):
    """按名字搜玩家（公开端点）：返回 [{name, tag, th, clan:{name,tag}}]。"""
    q = urllib.parse.quote(str(name))
    doc = _get("/v2/player/search?query=%s&limit=%d" % (q, int(limit)))
    out = []
    for it in doc.get("items") or []:
        clan = it.get("clan") or {}
        out.append({"name": it.get("name"), "tag": it.get("tag"),
                    "th": it.get("townHallLevel"),
                    "clan": {"name": clan.get("name"), "tag": clan.get("tag")}})
    return out


def search_clan(name, limit=5):
    """按名字搜部落（公开端点）：返回 [{name, tag, level, members}]。"""
    q = urllib.parse.quote(str(name))
    doc = _get("/v2/clan/search?query=%s&limit=%d" % (q, int(limit)))
    out = []
    for it in doc.get("items") or []:
        out.append({"name": it.get("name"), "tag": it.get("tag"),
                    "level": it.get("clanLevel"), "members": it.get("members")})
    return out


def resolve_opponent(name=None, clan_name=None):
    """OCR 出对手名字/部落名后的一步：名字 -> tag/TH/部落 -> 部落战成员 TH。"""
    res = {"query": {"name": name, "clan": clan_name}, "player": None, "clan": None, "war": None}
    if name:
        cands = search_player(name)
        if cands:
            res["player"] = cands[0]
    if clan_name:
        cands = search_clan(clan_name)
        if cands:
            res["clan"] = cands[0]
    elif res["player"] and res["player"]["clan"].get("tag"):
        res["clan"] = {"name": res["player"]["clan"].get("name"), "tag": res["player"]["clan"].get("tag")}
    if res["clan"] and res["clan"].get("tag"):
        try:
            res["war"] = war_members(res["clan"]["tag"])
        except Exception:
            res["war"] = None
    return res
'''
    t = t.rstrip() + "\n" + add
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("cocapi search added")
else:
    print("already present")

# CLI 增加 --search-name / --search-clan
p2 = os.path.join(BASE, "tools", "cocapi_cli.py")
t2 = open(p2, encoding="utf-8").read()
if "--search-name" not in t2:
    t2 = t2.replace('    ap.add_argument("--th", type=int, default=None)',
                    '    ap.add_argument("--th", type=int, default=None)\n'
                    '    ap.add_argument("--search-name", default=None, help="按玩家名字搜 tag/TH")\n'
                    '    ap.add_argument("--search-clan", default=None, help="按部落名字搜 tag")')
    t2 = t2.replace('    if a.auto_levels:',
'''    if a.search_name or a.search_clan:
        r = cocapi.resolve_opponent(a.search_name, a.search_clan)
        print(json.dumps(r, ensure_ascii=False, indent=1)[:2000])
    if a.auto_levels:''')
    open(p2, "w", encoding="utf-8", newline="\n").write(t2)
    print("cli search added")
