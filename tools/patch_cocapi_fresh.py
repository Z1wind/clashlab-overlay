# -*- coding: utf-8 -*-
"""cocapi 新鲜度 + OCR 模块 + CLI。"""
import os
BASE = r"C:\Users\Admin（无密码）\Doubao\chats\2026-11-23\new-chat"

# ---------- 1) cocapi 新鲜度 ----------
p = os.path.join(BASE, "clashlab", "cocapi.py")
t = open(p, encoding="utf-8").read()
if "def _get(path, ttl=TTL, fresh=False)" not in t:
    t = t.replace('''def _get(path, ttl=TTL):
    key = path
    now = time.time()
    hit = _cache.get(key)
    if hit and now - hit[0] < ttl:
        return hit[1]''',
'''def _get(path, ttl=TTL, fresh=False):
    """fresh=True 时强制回源，保证拿到的是最新数据（不吃缓存）。"""
    key = path
    now = time.time()
    hit = _cache.get(key)
    if hit and not fresh and now - hit[0] < ttl:
        return hit[1]''')
    t = t.replace('''def player_war_attacks(tag):
    return _get("/v2/player/%s/war/attacks" % _enc(tag)).get("items") or []''',
'''def player_war_attacks(tag, fresh=False):
    return _get("/v2/player/%s/war/attacks" % _enc(tag), ttl=120, fresh=fresh).get("items") or []''')
    t = t.replace('''def clan_wars(clan_tag):
    return _get("/v2/clan/%s/wars" % _enc(clan_tag)).get("items") or []''',
'''def clan_wars(clan_tag, fresh=False):
    return _get("/v2/clan/%s/wars" % _enc(clan_tag), ttl=30, fresh=fresh).get("items") or []''')
    t = t.replace('''def war_members(clan_tag, prefer_current=True):''',
'''def war_members(clan_tag, prefer_current=True, fresh=False):''')
    t = t.replace('''    wars = clan_wars(clan_tag)''', '''    wars = clan_wars(clan_tag, fresh=fresh)''')
    t = t.replace('''def player_th(tag):''', '''def player_th(tag, fresh=False):''')
    t = t.replace('''    items = player_war_attacks(tag)''', '''    items = player_war_attacks(tag, fresh=fresh)''')
    t = t.replace('''def search_player(name, limit=5):''', '''def search_player(name, limit=5, fresh=False):''')
    t = t.replace('''    doc = _get("/v2/player/search?query=%s&limit=%d" % (q, int(limit)))''',
                  '''    doc = _get("/v2/player/search?query=%s&limit=%d" % (q, int(limit)), ttl=120, fresh=fresh)''')
    t = t.replace('''def search_clan(name, limit=5):''', '''def search_clan(name, limit=5, fresh=False):''')
    t = t.replace('''    doc = _get("/v2/clan/search?query=%s&limit=%d" % (q, int(limit)))''',
                  '''    doc = _get("/v2/clan/search?query=%s&limit=%d" % (q, int(limit)), ttl=120, fresh=fresh)''')
    t = t.replace('''def resolve_opponent(name=None, clan_name=None):''', '''def resolve_opponent(name=None, clan_name=None, fresh=True):''')
    t = t.replace('''        cands = search_player(name)''', '''        cands = search_player(name, fresh=fresh)''')
    t = t.replace('''        cands = search_clan(clan_name)''', '''        cands = search_clan(clan_name, fresh=fresh)''')
    t = t.replace('''            res["war"] = war_members(res["clan"]["tag"])''',
                  '''            res["war"] = war_members(res["clan"]["tag"], fresh=fresh)''')
    t = t.replace('''def apply_th_levels(layout, th):''',
'''def cache_age(path):
    """返回该请求缓存年龄（秒）；没缓存返回 None。"""
    hit = _cache.get(path)
    return None if not hit else round(time.time() - hit[0], 1)


def apply_th_levels(layout, th):''')
    open(p, "w", encoding="utf-8", newline="\n").write(t)
    print("cocapi freshness patched")
else:
    print("cocapi already patched")
