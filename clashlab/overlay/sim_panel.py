# -*- coding: utf-8 -*-
"""P3c-3：2D 推演结果 → PANEL 研究页一行文案（纯函数 + 指纹缓存，不依赖 imgui）。

数据链（全部复用离线模块，不改其算法）：
  layout dict -> sim.Simulator -> analysis.deployment_ring -> analysis.defense_report
  -> analysis.candidate_plans(topk=3) -> top1
文案口径：「推演：预估摧毁 XX% · 最佳落点 (x,y)」。
  XX 取 top1["predicted_raw"]（模拟器热图均值，0..1 视为相对摧毁比例）×100 取整并
  clamp 到 0..100。刻意不用 top1["predicted"]——那是同批最优=1.0 的归一值，
  恒为 1.0，不能当摧毁率；predicted_raw 才是同批可比的原始热图均值。
  （clashlab/README.md:265 已声明 predicted 为相对排序，本行口径与之一致。）
无布局 / 无候选 / 计算异常 -> 「推演：无数据」。
缓存：按 layout 指纹（grid / 建筑数 / 墙数 / 首元素）命中，与 score_card 同口径；
03 阵全链实测 ~42ms，面板 60fps 下绝不允许每帧重算。
"""
from __future__ import annotations

import json
import time

EMPTY = {
    "available": False,
    "destroy_pct": None,
    "tile": None,
    "id": None,
    "name": "",
    "risk": "",
    "exposure": None,
    "timing_ms": None,
    "line": "推演：无数据",
}
NO_DATA = "推演：无数据"

_CACHE = {"key": None, "summary": None}


def _fingerprint(layout):
    """布局指纹：grid / 建筑数 / 墙数 / 首个建筑(type,tile)；与 score_card 同口径。"""
    try:
        b = layout.get("buildings") or []
        w = layout.get("walls") or []
        first_b = (b[0].get("type"), tuple(b[0].get("tile") or ())) if b else ("", ())
        return (layout.get("grid"), len(b), len(w), first_b)
    except Exception:
        return None


def _army_sig(army):
    if not army:
        return "default"
    try:
        return json.dumps(army, sort_keys=True, default=str)
    except Exception:
        return "default"


def _clamp_pct(v):
    """任意数值 -> 0..100 整数百分比（NaN / None 抛 TypeError/ValueError 由调用方兜）。"""
    f = float(v)
    if f != f:  # NaN
        return 0
    return max(0, min(100, int(round(f))))


def line_from_summary(summary):
    """sim 摘要 dict -> 一行中文文案；无数据统一「推演：无数据」。"""
    if not isinstance(summary, dict) or not summary.get("available"):
        return NO_DATA
    tile = summary.get("tile")
    pct = summary.get("destroy_pct")
    try:
        x = int(round(float(tile[0])))
        y = int(round(float(tile[1])))
        p = _clamp_pct(pct)
    except (TypeError, ValueError, IndexError, KeyError):
        return NO_DATA
    return f"推演：预估摧毁 {p}% · 最佳落点 ({x},{y})"


def summary_from_plans(plans):
    """analysis.candidate_plans 返回值 -> PANEL 摘要（top1 = plans[0]，已按 predicted 降序）。"""
    plans = plans or []
    if not plans:
        return dict(EMPTY)
    top = plans[0]
    try:
        entry = (top.get("entries") or [{}])[0]
        tile = entry.get("tile")
        x = int(round(float(tile[0])))
        y = int(round(float(tile[1])))
        raw = float(top.get("predicted_raw"))
    except (TypeError, ValueError, IndexError, KeyError):
        return dict(EMPTY)
    summary = {
        "available": True,
        "destroy_pct": _clamp_pct(raw * 100.0),
        "tile": [x, y],
        "id": top.get("id"),
        "name": top.get("name") or "",
        "risk": top.get("risk") or "",
        "exposure": top.get("exposure"),
        "timing_ms": None,
    }
    summary["line"] = line_from_summary(summary)
    return summary


def _sim_from_layout(layout, n=44):
    """layout dict -> Simulator（口径同 cli._sim_from_layout / prebattle 本地兜底）。"""
    from .. import assets
    from ..sim import Simulator

    sim = Simulator(n=n)
    for b in layout.get("buildings") or []:
        st = assets.STATS.get(b.get("type"), {})
        sim.add_building(b.get("type", "defense"), b.get("tile") or [0, 0],
                         b.get("hp", st.get("hp", 1400)),
                         b.get("dps", st.get("dps", 120)),
                         st.get("range", 9))
    walls = layout.get("walls") or []
    if walls:
        sim.add_wall([tuple(w) for w in walls])
    return sim


def build_summary(layout, army=None, n=44):
    """真实计算链（重函数，仅缓存 miss 时调用；异常 -> 无数据，绝不崩面板）。"""
    from .. import analysis, planner

    if not isinstance(layout, dict) or not (layout.get("buildings") or []):
        return dict(EMPTY)
    army = dict(army or planner.DEFAULT_ARMY)
    if not army.get("troops"):
        army["troops"] = dict(planner.DEFAULT_ARMY.get("troops") or {})
    t0 = time.perf_counter()
    sim = _sim_from_layout(layout, n=n)
    ring = analysis.deployment_ring(sim, margin=1)
    report = analysis.defense_report(sim, ring, army)
    plans = analysis.candidate_plans(sim, ring, army, report)
    summary = summary_from_plans(plans)
    summary["timing_ms"] = round((time.perf_counter() - t0) * 1000.0, 1)
    return summary


def summary_from_layout(layout, army=None, builder=None):
    """带指纹缓存的入口：同一 layout 只算一次（面板每帧调用）。"""
    fp = _fingerprint(layout)
    if fp is None:
        return dict(EMPTY)
    key = (fp, _army_sig(army))
    if _CACHE.get("key") == key and _CACHE.get("summary") is not None:
        return _CACHE["summary"]
    fn = builder or build_summary
    try:
        summary = fn(layout, army)
    except Exception:
        summary = dict(EMPTY)
    if not isinstance(summary, dict):
        summary = dict(EMPTY)
    summary.setdefault("line", line_from_summary(summary))
    _CACHE.update({"key": key, "summary": summary})
    return summary


def reset_cache():
    _CACHE.update({"key": None, "summary": None})
