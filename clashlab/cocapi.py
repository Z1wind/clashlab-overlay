# -*- coding: utf-8 -*-
"""ClashKing 公开 API 客户端：用玩家/部落标签自动拿 TH 等级与部落战成员。

思路借鉴 ClashKingBot：数据驱动而不是全靠图像。公开端点（无需 token）：
- GET /v2/player/{tag}/war/attacks   最近战争里的攻防记录（含 attackerTownhall / defenderTownhall）
- GET /v2/player/{tag}/war/stats     战争统计
- GET /v2/clan/{clan}/wars           最近/当前部落战，双方成员含 townhallLevel / mapPosition

拿不到的东西（需要官方 API token）：英雄等级、兵种等级、装备等级。
"""
from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request

API = "https://api.clashk.ing"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(ROOT, "out", "cache", "cocapi")
TTL = 60.0
_cache = {}


def _enc(tag):
    t = str(tag or "").strip()
    if not t:
        raise ValueError("tag 不能为空")
    if not t.startswith("#"):
        t = "#" + t
    return urllib.parse.quote(t)


def _get(path, ttl=TTL, fresh=False):
    """fresh=True 时强制回源，保证拿到的是最新数据（不吃缓存）。"""
    key = path
    now = time.time()
    hit = _cache.get(key)
    if hit and not fresh and now - hit[0] < ttl:
        return hit[1]
    req = urllib.request.Request(API + path, headers={"User-Agent": "clashlab", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=25) as r:
        doc = json.loads(r.read().decode("utf-8", "ignore"))
    _cache[key] = (now, doc)
    return doc


def player_war_attacks(tag, fresh=False):
    return _get("/v2/player/%s/war/attacks" % _enc(tag), ttl=120, fresh=fresh).get("items") or []


def player_th(tag, fresh=False):
    """推断玩家当前 TH：优先「最近一场战争」里的记录（玩家会升 TH，历史记录不可靠）。"""
    items = player_war_attacks(tag, fresh=fresh)
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
    return max(counts.items(), key=lambda kv: kv[1])[0]


def clan_wars(clan_tag, fresh=False):
    return _get("/v2/clan/%s/wars" % _enc(clan_tag), ttl=30, fresh=fresh).get("items") or []


def _members(side):
    out = []
    for m in (side or {}).get("members") or []:
        out.append({"tag": m.get("tag"), "name": m.get("name"), "th": m.get("townhallLevel"),
                    "pos": m.get("mapPosition")})
    return out


def war_members(clan_tag, prefer_current=True, fresh=False):
    """返回一场战争 {state, team_size, start_time, end_time, clan:{...}, opponent:{...}, members:[...]}。"""
    wars = clan_wars(clan_tag, fresh=fresh)
    if not wars:
        return None
    cur = [w for w in wars if str(w.get("state")) in ("inWar", "preparation")]
    w = cur[0] if (cur and prefer_current) else wars[0]
    return {"state": w.get("state"), "team_size": w.get("teamSize"),
            "start_time": w.get("startTime"), "end_time": w.get("endTime"),
            "clan": {"tag": (w.get("clan") or {}).get("tag"), "members": _members(w.get("clan"))},
            "opponent": {"tag": (w.get("opponent") or {}).get("tag"),
                         "members": _members(w.get("opponent"))}}


def enemy_th_map(clan_tag):
    """当前战争的对手成员 {tag: TH}（无当前战争则用最近一场）。"""
    w = war_members(clan_tag)
    if not w:
        return {}
    return {m["tag"]: m["th"] for m in w["opponent"]["members"] if m.get("tag")}


def cache_age(path):
    """返回该请求缓存年龄（秒）；没缓存返回 None。"""
    hit = _cache.get(path)
    return None if not hit else round(time.time() - hit[0], 1)


def apply_th_levels(layout, th):
    """把布局里每栋建筑的 level 按该 TH 的 reviewed 最高等级回填。"""
    from . import levels
    n = 0
    skipped = 0
    for b in (layout.get("buildings") or []):
        t = str(b.get("type") or "")
        lv = levels.max_level_of(t, th, strict=True)
        if lv is None:
            skipped += 1
            continue
        b["level"] = int(lv)
        n += 1
    return {"updated": n, "skipped": skipped, "th": int(th)}


def search_player(name, limit=5, fresh=False):
    """按名字搜玩家（公开端点）：返回 [{name, tag, th, clan:{name,tag}}]。"""
    q = urllib.parse.quote(str(name))
    doc = _get("/v2/player/search?query=%s&limit=%d" % (q, int(limit)), ttl=120, fresh=fresh)
    out = []
    for it in doc.get("items") or []:
        clan = it.get("clan") or {}
        out.append({"name": it.get("name"), "tag": it.get("tag"),
                    "th": it.get("townHallLevel"),
                    "clan": {"name": clan.get("name"), "tag": clan.get("tag")}})
    return out


def search_clan(name, limit=5, fresh=False):
    """按名字搜部落（公开端点）：返回 [{name, tag, level, members}]。"""
    q = urllib.parse.quote(str(name))
    doc = _get("/v2/clan/search?query=%s&limit=%d" % (q, int(limit)), ttl=120, fresh=fresh)
    out = []
    for it in doc.get("items") or []:
        out.append({"name": it.get("name"), "tag": it.get("tag"),
                    "level": it.get("clanLevel"), "members": it.get("members")})
    return out


def _norm_name(s):
    import re as _re
    s = str(s or "").lower()
    s = _re.sub(r"[^0-9a-z\u4e00-\u9fff]+", " ", s)
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


def _search_player_best(name, clan_name=None, ocr_level=None, fresh=True):
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
    return max(cands, key=score)


def _find_clan_with_member(player_name, clan_name=None, fresh=True, ocr_level=None):
    """按部落名搜候选，再在部落战成员里模糊匹配玩家名，返回 (clan, war, member)。"""
    cands = []
    if clan_name:
        norm = _norm_name(clan_name)
        words = norm.split()
        variants = [clan_name, norm, str(clan_name).title()]
        if len(words) > 1:
            variants += [" ".join(words[:2]), words[0]]
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
        war_bonus = 0.35 if str(war.get("state")) in ("inWar", "preparation") else 0.0
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
                    best = (sc, c, war, m)
    return best[1:] if best else (None, None, None)


def resolve_opponent(name=None, clan_name=None, fresh=True, ocr_level=None):
    """OCR 出对手名字/部落名后的一步：名字 -> tag/TH/部落 -> 部落战成员 TH。"""
    import time as _t
    if name and str(name).strip().startswith("#"):
        return resolve_by_tag(name, fresh=fresh)
    res = {"query": {"name": name, "clan": clan_name}, "player": None, "clan": None,
           "war": None, "matched_member": None, "match": None,
           "fetched_at": _t.strftime("%Y-%m-%dT%H:%M:%S"), "fresh": bool(fresh)}
    # 1) 先按名字找玩家（带兜底变体）
    pl = _search_player_best(name, clan_name=clan_name, ocr_level=ocr_level, fresh=fresh) if name else None
    if pl:
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

    if clan_name and pl and _name_score(clan_name, ((pl.get("clan") or {}).get("name") or "")) < 0.5:
        if res.get("match", {}).get("by") != "war-member-fuzzy":
            res["ambiguous"] = True
            res["warning"] = "同名/部落不匹配：请用玩家标签或点选候选确认"

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
        res["candidates"] = []
    # 2) 名字没找到，就用部落名找候选部落，再在战争成员里模糊匹配玩家
    if not pl and (name or clan_name):
        clan, war, member = _find_clan_with_member(name, clan_name, fresh=fresh, ocr_level=ocr_level)
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
    return res


def resolve_by_tag(tag, fresh=True):
    """OCR 到玩家 tag 时最可靠：直接按 tag 取 TH + 部落战。"""
    tag = "#" + str(tag).strip().lstrip("#").upper()
    th = player_th(tag, fresh=fresh)
    res = {"query": {"tag": tag}, "player": {"name": None, "tag": tag, "th": th},
           "clan": None, "war": None, "match": {"by": "player-tag"},
           "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "fresh": bool(fresh)}
    return res


# ---------------------------------------------------------------- 可选 token（拉布局库）
_TOKEN_FILE = os.path.join(ROOT, "config", "cocapi_token.txt")


def auth_token():
    """读 CLASHKING_TOKEN 环境变量或 config/cocapi_token.txt；都没有返回空串。"""
    tok = (os.environ.get("CLASHKING_TOKEN") or "").strip()
    if tok:
        return tok
    try:
        with open(_TOKEN_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""


def auth_headers():
    tok = auth_token()
    h = {"User-Agent": "clashlab", "Accept": "application/json"}
    if tok:
        h["Authorization"] = "Bearer " + tok
    return h


def _auth_get(path, timeout=25):
    """带可选 token 的 GET；401 时给出中文提示。"""
    req = urllib.request.Request(API + path, headers=auth_headers())
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", "ignore"))
    except urllib.error.HTTPError as e:
        if e.code == 401:
            raise RuntimeError("ClashKing 需要登录 token：把 UserToken 写入 config/cocapi_token.txt 或设 CLASHKING_TOKEN") from None
        raise


def personal_bases():
    """/v2/bases/personal：当前账号保存的阵型（需要 UserToken）。"""
    return _auth_get("/v2/bases/personal")


def server_bases(server_id):
    """/v2/server/{id}/bases：服务器布局库（需要 UserToken/BotToken）。"""
    return _auth_get("/v2/server/%s/bases" % urllib.parse.quote(str(server_id)))
