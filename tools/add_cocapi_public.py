# -*- coding: utf-8 -*-
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"
p = os.path.join(BASE, "clashlab", "cocapi.py")
t = open(p, encoding="utf-8").read()
if "def clan_cached(" not in t:
    anchor = "def clan_wars(clan_tag, fresh=False):"
    add = '''def clan_cached(clan_tag, fresh=False):
    """公开缓存部落档案（无需 token）：含 members[{tag,name,townHallLevel}]、warLeague 等。
    注意：仅 ClashKing 已收录的部落有数据，未收录返回空 dict 或 null。"""
    doc = _get("/v2/clan/%s/cached" % _enc(clan_tag), ttl=60, fresh=fresh)
    return doc if isinstance(doc, dict) else {}


def cached_members_th(clan_tag, fresh=False):
    """{player_tag: townHallLevel}，来自 cached 档案（无 token 路径）。"""
    doc = clan_cached(clan_tag, fresh=fresh)
    out = {}
    for m in doc.get("members") or []:
        tag = str(m.get("tag") or "").upper()
        th = m.get("townHallLevel")
        if tag and isinstance(th, int):
            out[tag] = th
    return out


def clan_wars_filtered(clan_tag, war_type=None, limit=10, fresh=False):
    """带筛选的战争列表：war_type 例如 cwl / regular；不传则用默认。"""
    path = "/v2/clan/%s/wars?limit=%d" % (_enc(clan_tag), int(limit))
    if war_type:
        path += "&type=%s" % _enc_url(war_type)
    return _get(path, ttl=60, fresh=fresh).get("items") or []


def static_names(category):
    """静态数据类别的名称列表：troops/buildings/spells/heroes/pets/equipment。"""
    doc = _get("/v2/static/%s/names" % _enc_url(category), ttl=86400)
    return doc if isinstance(doc, list) else []


def static_max_level(category, name):
    """单个静态数据项的最高等级，例如 ('buildings','Town Hall') -> 19。"""
    doc = _get("/v2/static/%s/%s/max-level" % (_enc_url(category), _enc_url(name)), ttl=86400)
    return (doc or {}).get("max_level")


def _enc_url(s):
    import urllib.parse
    return urllib.parse.quote(str(s), safe="")


'''
    if anchor in t:
        t = t.replace(anchor, add + anchor, 1)
        open(p, "w", encoding="utf-8", newline="\n").write(t)
        print("cocapi public helpers added")
    else:
        print("anchor miss")
else:
    print("already")
