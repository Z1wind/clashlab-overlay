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


def _get(path, ttl=TTL):
    key = path
    now = time.time()
    hit = _cache.get(key)
    if hit and now - hit[0] < ttl:
        return hit[1]
    req = urllib.request.Request(API + path, headers={"User-Agent": "clashlab", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=25) as r:
        doc = json.loads(r.read().decode("utf-8", "ignore"))
    _cache[key] = (now, doc)
    return doc


def player_war_attacks(tag):
    return _get("/v2/player/%s/war/attacks" % _enc(tag)).get("items") or []


def player_th(tag):
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
    return max(counts.items(), key=lambda kv: kv[1])[0]


def clan_wars(clan_tag):
    return _get("/v2/clan/%s/wars" % _enc(clan_tag)).get("items") or []


def _members(side):
    out = []
    for m in (side or {}).get("members") or []:
        out.append({"tag": m.get("tag"), "name": m.get("name"), "th": m.get("townhallLevel"),
                    "pos": m.get("mapPosition")})
    return out


def war_members(clan_tag, prefer_current=True):
    """返回一场战争 {state, team_size, start_time, end_time, clan:{...}, opponent:{...}, members:[...]}。"""
    wars = clan_wars(clan_tag)
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
