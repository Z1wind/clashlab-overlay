# -*- coding: utf-8 -*-
"""规则化阵型评分：每条规则可解释（通过/失败 + 证据 + 建议），替代黑箱加权分。"""
from __future__ import annotations
import math

from .layout_grid import LayoutGrid

AIR = {"air-defense", "air-sweeper"}
STORAGE = {"gold-storage", "elixir-storage", "dark-elixir-storage"}


def _center(b):
    t = b.get("tile") or [0, 0]
    return float(t[0]) + 1.5, float(t[1]) + 1.5


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _rule(rid, title, severity, passed, evidence, rec, skipped=False):
    return {"id": rid, "title": title, "severity": severity, "passed": bool(passed),
            "skipped": bool(skipped), "evidence": evidence,
            "recommendation": None if (passed or skipped) else rec}


def evaluate(layout: dict) -> dict:
    blds = layout.get("buildings") or []
    grid = LayoutGrid.from_layout(layout)
    bmap = {}
    for b in blds:
        p = _center(b)
        bmap.setdefault(b.get("type") or "unknown", []).append(p)
    th = bmap.get("town-hall") or []
    rules = []

    comps = grid.compartments(min_tiles=4)
    wall_conf = "high" if len(comps) >= 1 else "low"  # 墙数据不闭合时，墙类规则只提示不判负
    # R1 大本是否被墙围
    _th_ok = grid.th_inside_walls()
    rules.append(_rule("R1", "大本被墙保护", "critical", _th_ok,
                       ("闭合隔间内的主堡" if _th_ok else "大本不在任何闭合墙体内")
                       if wall_conf == "high" else "墙数据不完整（无闭合隔间），该规则未判定",
                       "给大本围一圈闭合墙，至少覆盖 3 面", skipped=(wall_conf != "high")))

    # R2 大本中心度
    if th:
        cx, cy = th[0]
        d = math.hypot(cx - 22.0, cy - 22.0)
        rules.append(_rule("R2", "大本居中", "warn", d <= 8.0, "距地图中心 %.1f 格" % d,
                           "把大本移向中心（当前偏心 %.1f 格）" % d))
    else:
        rules.append(_rule("R2", "大本居中", "warn", False, "未标注大本", "标注大本位置"))

    # R3 对空覆盖核心
    if bmap.get("air-defense"):
        near = min(_dist(th[0], p) for p in bmap["air-defense"]) if th else 99
        rules.append(_rule("R3", "防空覆盖大本", "critical", near <= 12.0, "最近防空距大本 %.1f 格" % near,
                           "至少一座防空火箭靠近大本（≤12 格）"))
    else:
        rules.append(_rule("R3", "防空覆盖大本", "critical", False, "无防空火箭", "补防空火箭"))

    # R4 吹风机覆盖
    if bmap.get("air-sweeper"):
        near = min(_dist(th[0], p) for p in bmap["air-sweeper"]) if th else 99
        rules.append(_rule("R4", "吹风机威胁核心", "warn", near <= 14.0, "最近吹风机距大本 %.1f 格" % near,
                           "吹风机应能罩住核心区"))
    else:
        rules.append(_rule("R4", "吹风机威胁核心", "warn", False, "无吹风机", "考虑放吹风机"))

    # R5 隔间数量（墙结构质量）
    rules.append(_rule("R5", "墙隔间 ≥4", "warn", len(comps) >= 4,
                       "闭合隔间 %d 个" % len(comps),
                       "用墙分出更多隔间（≥4），拖慢地面部队", skipped=(wall_conf != "high")))

    # R6 墙体连贯
    iso = grid.wall_efficiency()
    rules.append(_rule("R6", "墙体连贯", "warn", iso <= 0.25, "孤立墙比例 %.0f%%" % (iso * 100),
                       "把断墙连成闭合圈（孤立墙 %.0f%%）" % (iso * 100), skipped=(wall_conf != "high")))

    # R7 资源仓不暴露边缘
    _all_storages = []
    for _t in STORAGE:
        _all_storages.extend(bmap.get(_t) or [])
    edge_storages = [p for p in _all_storages if min(p[0], p[1], 44 - p[0], 44 - p[1]) <= 3]
    rules.append(_rule("R7", "仓库不贴边", "warn", not edge_storages,
                       "贴边仓库 %d 个" % len(edge_storages), "把仓库拉进内圈"))

    # R8 防御分散（大本附近不能只有一种防御）
    defs = [(t, p) for t, ps in bmap.items() for p in ps
            if t not in ("town-hall", "gold-mine", "elixir-collector", "dark-elixir-drill", "wall")]
    near_core = [t for t, p in defs if _dist(p, (22.0, 22.0)) <= 12]
    kinds = len(set(near_core))
    rules.append(_rule("R8", "核心区防御多样", "info", kinds >= 4, "核心 12 格内防御种类 %d" % kinds,
                       "核心区防御类型偏少（%d 种），补多样性" % kinds))

    # 汇总
    weight = {"critical": 3, "warn": 2, "info": 1}
    scored = [r for r in rules if not r.get("skipped")]
    total = sum(weight[r["severity"]] for r in scored)
    got = sum(weight[r["severity"]] for r in scored if r["passed"])
    score = round(100.0 * got / total, 1) if total else 0.0
    grade = "S" if score >= 85 else "A" if score >= 70 else "B" if score >= 60 else "C" if score >= 50 else "D"
    return {"score": score, "grade": grade, "rules": rules, "wall_confidence": wall_conf,
            "skipped": [r["id"] for r in rules if r.get("skipped")],
            "failed": [r for r in rules if (not r["passed"] and not r.get("skipped"))],
            "wall_compartments": len(comps), "wall_isolated_ratio": round(iso, 3),
            "validator_issues": grid.validate()}
