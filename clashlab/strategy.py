# -*- coding: utf-8 -*-
"""布阵 → 兵种搭配推荐 + 打法搜索链接。

流程：defense_findings / layout_score 抽弱点 → 归因到 reason
（air-gap / th-bias / compartment-density / general）→ 从 knowledge/strategies.json
选模板 → 输出 archetype、troops、why、steps、videos（YouTube 搜索页，不抓取内容）。
"""
from __future__ import annotations

import json
import os
import re
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_STRATEGIES = os.path.join(ROOT, "knowledge", "strategies.json")
DATA_HEROES = os.path.join(ROOT, "knowledge", "hero_equipment.json")
YT = YOUTUBE_SEARCH = "https://www.youtube.com/results?search_query="

REASON_ARCH = {"air-gap": "air", "th-bias": "hero-dive",
               "compartment-density": "ground", "general": "hybrid"}
REASON_LABEL = {"air-gap": "对空覆盖不足", "th-bias": "大本营偏离中心",
                "compartment-density": "隔间/墙体密集", "general": "无明显可打弱点"}

# 数据文件把法术也写在 troops_by_th 里；输出时拆成 troops / spells 两块。
SPELL_IDS = {
    "rage", "freeze", "heal", "jump", "haste", "clone", "poison",
    "earthquake", "invisibility", "skeleton", "bat", "recall", "revive",
}
TROOP_NAMES_ZH = {
    "edrag": "雷龙", "electro-dragon": "雷龙", "dragon": "飞龙",
    "balloon": "气球", "lava-hound": "熔岩猎犬", "baby-dragon": "龙宝",
    "hog-rider": "野猪骑士", "miner": "矿工", "super-witch": "超级女巫",
    "witch": "女巫", "ice-golem": "冰戈仑", "super-wizard": "超级法师",
    "root-rider": "根骑士", "dragon-rider": "龙骑士", "yeti": "雪怪",
    "bat": "蝙蝠", "healer": "天使", "electro-titan": "雷电泰坦",
    "golem": "戈仑石人", "pekka": "皮卡超人", "valkyrie": "女武神",
    "bowler": "投球手", "wizard": "法师", "archer": "弓箭手",
    "barbarian": "野蛮人", "giant": "巨人", "wall-breaker": "炸弹人",
}
SPELL_NAMES_ZH = {
    "rage": "狂暴", "freeze": "冰冻", "heal": "治疗", "jump": "弹跳",
    "haste": "急速", "clone": "克隆", "poison": "毒药", "earthquake": "地震",
    "invisibility": "隐形", "skeleton": "骷髅", "bat": "蝙蝠",
    "recall": "回溯", "revive": "复活",
}
HERO_NAMES_ZH = {
    "queen": "弓箭女皇", "king": "野蛮人之王", "warden": "大守护者",
    "royal-champion": "皇家冠军", "minion-prince": "亡灵王子",
}


def load_strategies(path=None):
    with open(path or DATA_STRATEGIES, encoding="utf-8") as f:
        return json.load(f)


def load_hero_equipment(path=None):
    with open(path or DATA_HEROES, encoding="utf-8") as f:
        return json.load(f)


def load_layout(src):
    """layout dict 或 json 路径 -> dict；None -> {}。"""
    if src is None:
        return {}
    if isinstance(src, dict):
        return src
    with open(src, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("layout 必须是 JSON 对象")
    return data


def _metrics(layout):
    lay = load_layout(layout)
    if not (lay.get("buildings") or []):
        return {}
    try:
        from . import layout_score
        return layout_score.score_layout(lay)
    except Exception:
        return {}


def _findings(layout):
    lay = load_layout(layout)
    if not (lay.get("buildings") or []):
        return []
    try:
        from . import defense_findings
        return defense_findings.findings(lay)
    except Exception:
        return []


def detect_signals(layout):
    """返回 (reason, signals list[dict])。确定性。"""
    lay = load_layout(layout)
    buildings = [b for b in (lay.get("buildings") or []) if isinstance(b, dict)]
    res = _metrics(lay)
    findings = _findings(lay)
    metrics = res.get("metrics") or []

    def _metric(mid):
        return next((m for m in metrics if m.get("id") == mid), {}) or {}

    air_score = float(_metric("air-coverage").get("score", 0.0) or 0.0)
    ground_score = float(_metric("ground-coverage").get("score", 0.0) or 0.0)
    th_centrality = float(
        (_metric("town-hall-protection").get("details") or {}).get("centrality", 0.0) or 0.0)
    comp = _metric("compartment-quality").get("details") or {}
    compartments = int(comp.get("compartments", 0) or 0)
    useful = int(comp.get("useful", 0) or 0)
    has_th = any(b.get("type") == "town-hall" for b in buildings)
    defense_count = 0
    try:
        from . import layout_score
        defense_count = sum(1 for b in buildings if b.get("type") in layout_score.DEFENSE_TABLE)
    except Exception:
        pass
    signals = [
        {"name": "air-coverage", "value": round(air_score, 1)},
        {"name": "ground-coverage", "value": round(ground_score, 1)},
        {"name": "th-centrality", "value": round(th_centrality, 3)},
        {"name": "compartments", "value": compartments},
        {"name": "useful-compartments", "value": useful},
        {"name": "defenses", "value": defense_count},
        {"name": "walls", "value": len(lay.get("walls") or [])},
    ]

    # 空布局 / 没有防御建筑：无法判定，给通用推荐。
    if not buildings or defense_count == 0:
        return "general", signals

    air_weak = any(f.get("key") == "air-coverage" and f.get("severity") in ("weak", "critical")
                   for f in findings) or air_score < 90.0
    th_bias = has_th and (
        any(f.get("key") == "town-hall-protection"
            and f.get("severity") in ("weak", "critical") for f in findings)
        or th_centrality < 0.85)
    dense = useful >= 5 or compartments >= 6 or any(
        "隔间" in str(f.get("text") or "") for f in findings)

    if air_weak:
        reason = "air-gap"
    elif th_bias:
        reason = "th-bias"
    elif dense:
        reason = "compartment-density"
    else:
        reason = "general"
    return reason, signals


def _why_text(reason, layout, base):
    lay = load_layout(layout)
    res = _metrics(lay)
    metrics = res.get("metrics") or []

    def _metric(mid):
        return next((m for m in metrics if m.get("id") == mid), {}) or {}

    air = float(_metric("air-coverage").get("score", 0.0) or 0.0)
    ground = float(_metric("ground-coverage").get("score", 0.0) or 0.0)
    th = float((_metric("town-hall-protection").get("details") or {}).get("centrality", 0.0) or 0.0)
    comp = _metric("compartment-quality").get("details") or {}
    compartments = int(comp.get("compartments", 0) or 0)
    useful = int(comp.get("useful", 0) or 0)
    dead = int(comp.get("deadZones", 0) or 0)

    if reason == "air-gap":
        detail = "对空覆盖 %.0f%%" % air
        for f in _findings(lay):
            if f.get("key") == "air-coverage":
                detail = str(f.get("text") or detail)
                break
        return "%s（模板：%s）" % (detail, base)
    if reason == "th-bias":
        detail = "大本营中心度 %.2f" % th
        for f in _findings(lay):
            if f.get("key") == "town-hall-protection":
                detail = str(f.get("text") or detail)
                break
        return "%s（模板：%s）" % (detail, base)
    if reason == "compartment-density":
        detail = ("闭合隔间 %d 个（有效 %d 个，死区 %d 个）→ 地面强拆可逐间隔间清防御"
                  % (compartments, useful, dead))
        return "%s（模板：%s）" % (detail, base)
    if not (lay.get("buildings") or []):
        detail = "布局为空或缺少建筑数据，无法判定弱点"
    else:
        detail = ("无明显短板（对空 %.0f%% / 对地 %.0f%% / 大本营中心度 %.2f / 有效隔间 %d）"
                  % (air, ground, th, useful))
    return "%s（模板：%s）" % (detail, base)


def _videos(queries, th, troops=None):
    out = []
    # 第一条由「兵种 + TH」自动生成，后面再附策划好的固定查询。
    if troops:
        top = sorted(troops.items(), key=lambda kv: (-int(kv[1]), str(kv[0])))[:2]
        names = [TROOP_NAMES_ZH.get(str(k), str(k)) for k, _ in top]
        query = "TH%d %s 打法" % (int(th), " ".join(names) if names else "通用进攻")
        out.append({"title": "YouTube 搜索：" + query,
                    "url": YT + urllib.parse.quote_plus(query)})
    for q in (queries or [])[:3]:
        if len(out) >= 3:
            break
        text = str(q or "").strip()
        text = re.sub(r"TH\s*\d{1,2}", "TH%d" % int(th), text, flags=re.I)
        if not re.search(r"TH\s*%d\b" % int(th), text, re.I):
            text = "TH%d %s" % (int(th), text)
        url = YT + urllib.parse.quote_plus(text)
        if any(v["url"] == url for v in out):
            continue
        out.append({"title": "YouTube 搜索：" + text, "url": url})
    if not out:
        text = "TH%d clash of clans attack strategy" % int(th)
        out.append({"title": "YouTube 搜索：" + text, "url": YT + urllib.parse.quote_plus(text)})
    return out[:3]


def _general_rec(th, layout, reason="general"):
    """数据缺该 TH / 无法判定时的兜底推荐（reason 固定 general）。"""
    troops = {"giant": 12, "wizard": 10, "archer": 20}
    return {
        "id": "general-balanced",
        "name": "通用平衡进攻（信息不足）",
        "archetype": "hybrid",
        "reason": "general",
        "th": int(th),
        "why": _why_text("general", layout, "坦克开路 + 远程输出"),
        "troops": troops,
        "spells": {"heal": 2, "rage": 1},
        "steps": ["坦克开路", "远程跟进", "治疗覆盖核心", "英雄收尾"],
        "videos": _videos(["clash of clans attack basics guide"], th, troops),
        "source": "baseline",
        "confidence": 0.3,
        "matched_signals": [],
    }


def recommend(layout, th=None, limit=3):
    """返回推荐列表（按匹配度排序，同输入同输出）。"""
    layout = load_layout(layout)
    th = int(th or 16)
    reason, signals = detect_signals(layout)
    arch = REASON_ARCH[reason]
    data = load_strategies()
    cands = []
    for order, s in enumerate(data.get("strategies") or []):
        tb = s.get("troops_by_th") or {}
        if str(th) not in tb:
            continue
        tags = list(s.get("weakness_tags") or [])
        hit = (reason in tags) or (reason == "general" and "general" in tags)
        base_score = float(s.get("confidence") or 0) + (0.5 if hit else 0.0)
        if s.get("archetype") == arch:
            base_score += 0.4
        cands.append((base_score, order, s, hit))
    cands.sort(key=lambda x: (-x[0], x[1]))
    if not cands:
        return [_general_rec(th, layout, reason)]
    out = []
    for score, order, s, hit in cands[:max(1, int(limit))]:
        raw = {}
        for k, v in (s["troops_by_th"][str(th)] or {}).items():
            try:
                n = int(v)
            except (TypeError, ValueError):
                continue
            if n > 0:
                raw[str(k)] = n
        troops = {k: v for k, v in raw.items() if k not in SPELL_IDS}
        spells = {k: v for k, v in raw.items() if k in SPELL_IDS}
        out.append({
            "id": s.get("id"), "name": s.get("name"), "archetype": s.get("archetype"),
            "reason": reason, "th": th,
            "why": _why_text(reason, layout, s.get("why") or ""),
            "troops": troops, "spells": spells,
            "steps": list(s.get("steps") or [])[:5],
            "videos": _videos(s.get("video_queries"), th, raw),
            "source": s.get("source") or "community-meta",
            "confidence": float(s.get("confidence") or 0.5),
            "matched_signals": [reason] if hit else [],
        })
    return out


def hero_guides(th=None):
    th = int(th or 16)
    data = load_hero_equipment()
    recs = data.get("recommendations") or {}
    return [{"hero": h, **v} for h, v in (recs.get(str(th)) or {}).items()]


def hero_loadout(th=None):
    """TH -> {reference_only, disclaimer, heroes}（只读骨架）。"""
    th = int(th or 16)
    data = load_hero_equipment()
    recs = data.get("recommendations") or {}
    return {
        "th": th,
        "reference_only": True,
        "disclaimer": str(data.get("disclaimer") or ""),
        "heroes": dict(recs.get(str(th)) or {}),
    }
